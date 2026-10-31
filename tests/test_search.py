"""Rating-first search pagination and request-saving behavior, without network."""
import unittest
from urllib.parse import parse_qs, urlsplit

from tabelog_client.cli import run
from tabelog_client.core import CliError
from tabelog_client.service import Tabelog
from tabelog_client.transport import Client


ROOT = 'https://tabelog.com'


def marker(n, score=3.8, lat=.001, lon=0, cuisine='寿司'):
    return (f'<marker id="170000{n:02}" rstname="店{n}" '
            f'rsturl="/ishikawa/A1701/A170101/170000{n:02}/" '
            f'score="{score}" lat="{lat}" lng="{lon}" rstcat="{cuisine}"/>')


def map_page(*rows, more=True, total=60):
    return f'<markers><srchinfo cnt="{total}" nextpg="{2 if more else ""}"/>'+''.join(rows)+'</markers>'


def make_client(reader):
    def read(url):
        return {'body': reader(url), 'url': url, 'http_status': 200, 'version': 'test'}
    return Client(reader=read, delay_min_ms=0, delay_max_ms=0)


class SearchTests(unittest.TestCase):
    def test_cli_prefers_score_to_distance_and_stops_on_first_page(self):
        calls = []
        def read(url):
            calls.append(url)
            self.assertEqual(parse_qs(urlsplit(url).query)['SrtT'], ['rt'])
            return map_page(marker(1, 4.3, .008), marker(2, 3.9, .001), marker(3, 3.6, 0))
        result = run(['search', '--near', '0,0', '--pages', '10', '--limit', '2'],
                     create_client=lambda **kw: make_client(read))
        self.assertEqual(result['output']['status'], 'ok')
        data = result['output']['data']
        self.assertEqual([r['id'] for r in data['items']], ['17000001', '17000002'])
        self.assertGreater(data['items'][0]['distance_m'], data['items'][1]['distance_m'])
        self.assertEqual(len(calls), 1)
        self.assertEqual(data['meta']['pages_read'], 1)
        self.assertEqual(data['meta']['stop_reason'], 'limit_reached')
        self.assertEqual(data['meta']['sort'], 'rating_desc')

    def test_all_filters_and_deduplication_before_counting_limit(self):
        calls = []
        pages = [map_page(marker(1, 4.8, .008, .008), marker(2, 4.5, cuisine='ラーメン'),
                          marker(3, 4.0)),
                 map_page(marker(3, 4.0), marker(4, 3.9), marker(5, 3.4))]
        def read(url):
            calls.append(url)
            return pages[int(parse_qs(urlsplit(url).query)['pg'][0])-1]
        r = Tabelog(make_client(read)).search(near='0,0', min_rating=3.5,
                                              cuisines=['寿司'], limit=2, pages=10)
        self.assertEqual([x['id'] for x in r['items']], ['17000003', '17000004'])
        self.assertEqual(len(calls), 2)
        self.assertEqual(r['meta']['scanned_count'], 6)
        self.assertEqual(r['meta']['candidates_checked'], 4)

    def test_native_awards_and_meal_checks_continue_to_next_page_then_stop_details(self):
        calls, details = [], []
        pages = [map_page(marker(1, 4.5), marker(2, 4.4)),
                 map_page(marker(3, 4.3), marker(4, 4.2), marker(5, 4.1))]
        def read(url):
            calls.append(url)
            if 'hyakumeiten-category-list' in url:
                return '{"hyakumeitenCategoryList":[{"id":991,"name":"寿司"}]}'
            return pages[int(parse_qs(urlsplit(url).query)['pg'][0])-1]
        app = Tabelog(make_client(read))
        def detail(url):
            n = int(url.rstrip('/').split('/')[-1][-2:])
            details.append(n)
            if n == 2:
                raise CliError('unexpected_response', 'No recognized hours')
            return {'name': f'店{n}', 'cuisines': ['寿司'],
                    'hours': [{'closed': False, 'dayList': [1], 'rangeList':
                               [{'open': 1080, 'close': 1200} if n == 1 else {'open': 720, 'close': 840}]}]}
        app.detail = detail
        r = app.search(near='0,0', meal='lunch', hyakumeiten=True, limit=1, pages=10)
        self.assertEqual([x['id'] for x in r['items']], ['17000003'])
        self.assertEqual(details, [1, 2, 3])
        self.assertEqual(len(calls), 3)
        self.assertEqual(len(r['unverified']), 1)
        self.assertEqual(r['meta']['meal_check']['stopped_at_limit'], True)

    def test_meal_exclusions_do_not_count_toward_limit(self):
        calls, checked = [], []
        def read(url):
            calls.append(url)
            page = int(parse_qs(urlsplit(url).query)['pg'][0])
            return (map_page(marker(1, 4.7, cuisine='和菓子'), marker(2, 4.5), marker(3, 4.4))
                    if page == 1 else map_page(marker(4, 4.3), marker(5, 4.2)))
        app = Tabelog(make_client(read))
        def detail(url):
            n = int(url.rstrip('/').split('/')[-1][-2:])
            checked.append(n)
            return {'name': f'店{n}', 'cuisines': ['寿司'], 'hours': [] if n == 3 else
                    [{'closed': False, 'dayList': [1], 'rangeList':
                      [{'open': 1080 if n == 2 else 720, 'close': 1200 if n == 2 else 840}]}]}
        app.detail = detail
        r = app.search(near='0,0', meal='lunch', pages=10, limit=1)
        self.assertEqual([x['id'] for x in r['items']], ['17000004'])
        self.assertEqual(checked, [2, 3, 4])
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(r['meta']['meal_check']['excluded']), 2)
        self.assertEqual(len(r['unverified']), 1)

    def test_stops_at_page_budget_or_source_exhaustion_without_relaxing_filters(self):
        for more, expected in [(True, 'page_limit'), (False, 'source_exhausted')]:
            calls = []
            def read(url):
                calls.append(url)
                return map_page(marker(1, 3.4), more=more, total=1 if not more else 60)
            r = Tabelog(make_client(read)).search(near='0,0', min_rating=3.5, pages=1 if more else 10)
            self.assertEqual(r['items'], [])
            self.assertEqual(r['meta']['stop_reason'], expected)
            self.assertEqual(len(calls), 1)

    def test_area_search_stops_after_enough_filtered_results(self):
        calls = []
        def read(url):
            calls.append(url)
            page = 2 if '/rstLst/2/' in url else 1
            self.assertEqual(parse_qs(urlsplit(url).query)['SrtT'], ['rt'])
            return (f'<span class="c-pagination__num is-current">{page}</span>'
                    f'<span class="c-page-count__num"><strong>{1 if page == 1 else 21}</strong>'
                    f'<strong>{20 if page == 1 else 40}</strong><strong>60</strong></span>'
                    f'<div class="list-rst js-list-item" data-rst-id="1700000{page}" '
                    f'data-detail-url="/ishikawa/A1701/A170101/1700000{page}/">'
                    '<a class="list-rst__rst-name-target">店</a>'
                    f'<span class="list-rst__rating-val">{3.4 if page == 1 else 3.8}</span></div>')
        app = Tabelog(make_client(read))
        app.suggest = lambda query: [{'name': '金沢', 'kind': 'area', 'datatype': 'Area2', 'exact_match': True}]
        r = app.search(area='金沢', min_rating=3.5, pages=10, limit=1)
        self.assertEqual([x['id'] for x in r['items']], ['17000002'])
        self.assertEqual(len(calls), 2)
        self.assertEqual(r['meta']['stop_reason'], 'limit_reached')

    def test_access_denial_does_not_trigger_area_fallback(self):
        calls = []
        def read(url):
            calls.append(url)
            raise CliError('access_denied', '403')
        app = Tabelog(make_client(read))
        with self.assertRaises(CliError) as raised:
            app.search(near='0,0', area='金沢', pages=10)
        self.assertEqual(raised.exception.code, 'access_denied')
        self.assertEqual(len(calls), 1)
