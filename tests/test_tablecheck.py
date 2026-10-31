"""Offline behavioral checks for batched dates, scoped inventory and bounded reads."""
from datetime import datetime, timedelta, timezone
import json
import unittest

import httpx

from tablecheck_client.cli import run
from tablecheck_client.service import TableCheck, slug_value
from tablecheck_client.transport import Client, CliError


SHOP = {'_id': '1'*24, 'slug': 'sample-restaurant', 'time_zone': 'Asia/Tokyo', 'currency': 'JPY', 'booking_page_mode': 'v1',
        'name_translations': [{'locale': 'ja', 'translation': '例示店'}], 'geocode': {'lat': 36.5, 'lon': 136.5},
        'service_categories': [{'id': 'private', 'name_translations': [{'locale': 'en', 'translation': 'Private'}]}]}
COURSE = {'id': '2'*24, 'price': '55000.0', 'is_active': True, 'is_group_order': True, 'meals': ['dinner'],
          'service_category_ids': ['private'], 'valid_date_ranges': [{'start_date': '2026-12-01', 'end_date': '2026-12-31'}]}


def client(handler, budget=20):
    return Client(session=httpx.Client(transport=httpx.MockTransport(handler)), delay_min_ms=0, delay_max_ms=0, max_requests=budget)


def response(value):
    return httpx.Response(200, json=value)


def calendar(day, available=False):
    start = datetime.fromisoformat(day+'T08:00:00+00:00')
    return {(start+timedelta(minutes=i*30)).isoformat(): {'is_available': available and i == 2} for i in range(9)}


class TableCheckTests(unittest.TestCase):
    def test_calendar_reuses_one_response_for_a_month_and_filters_alternatives(self):
        def handler(request):
            if '/shops/' in request.url.path:
                return response({'shops': [SHOP]})
            data = {f'2026-12-{day:02}': calendar(f'2026-12-{day:02}', day == 2) for day in range(1, 31)}
            return response({'availability_calendar': {'type': 'success', 'time_zone': 'Asia/Tokyo', 'data': data,
                'closed_dates': [], 'alternate_timeslots': {'2026-12-01': ['2026-12-01T03:00:00Z']}}})
        transport = client(handler)
        result = TableCheck(transport).availability(SHOP['slug'], '2026-12-01', '2026-12-30', 2, '17:00', '21:00')
        self.assertEqual(transport.requests, 2)
        self.assertEqual(result['coverage'], 'complete')
        self.assertEqual(result['days'][1]['offered_times'], ['18:00'])
        self.assertEqual(result['days'][0]['offered_times'], [])
        transport.close()

    def test_missing_calendar_dates_remain_unknown_without_daily_sweep(self):
        def handler(request):
            return response({'shops': [SHOP]}) if '/shops/' in request.url.path else response(
                {'availability_calendar': {'type': 'success', 'time_zone': 'Asia/Tokyo', 'data': {'2026-12-01': calendar('2026-12-01')}, 'closed_dates': []}})
        transport = client(handler)
        result = TableCheck(transport).availability(SHOP['slug'], '2026-12-01', '2026-12-30', 2, '17:00', '21:00')
        self.assertEqual(transport.requests, 3)
        self.assertEqual(result['coverage'], 'partial')
        self.assertEqual(result['days'][-1]['status'], 'unknown')
        transport.close()

    def test_filtered_course_uses_form_index_and_batches_dates_then_confirms(self):
        seen = []
        def handler(request):
            seen.append(request)
            path = request.url.path
            if '/v2/shops/' in path:
                return response({'shops': [SHOP]})
            if path.endswith('/menu_items'):
                return response({'menu_items': [COURSE]})
            if path.endswith('/reserve'):
                return httpx.Response(200, text='<input name="reservation[service_category]" value="private">'
                    '<input name="reservation[orders_attributes][7][menu_item_id]" value="'+COURSE['id']+'">'
                    '<input name="reservation[orders_attributes][7][is_group_order]" value="true">')
            self.assertEqual(request.url.params['reservation[orders_attributes][7][menu_item_id]'], COURSE['id'])
            self.assertEqual(request.url.params['reservation[service_category]'], 'private')
            if path.endswith('/timetable'):
                return response({'queried_date': '2026-12-01', 'data': {'slots': {
                    day: {str(int(datetime.fromisoformat(day+'T09:00:00+00:00').timestamp())): {'available': True}}
                    for day in ('2026-12-01', '2026-12-02')}}})
            return response({'status': 'success'})
        transport = client(handler)
        result = TableCheck(transport).availability(SHOP['slug'], '2026-12-01', '2026-12-02', 2, '17:00', '21:00', COURSE['id'], 'Private')
        self.assertEqual(transport.requests, 6)
        self.assertEqual(sum(r.url.path.endswith('/timetable') for r in seen), 1)
        self.assertTrue(result['course_linked'] and result['seat_linked'])
        self.assertTrue(all(day['offered_times'] == ['18:00'] for day in result['days']))
        transport.close()

    def test_denial_stops_further_requests_and_reports_no_empty_inventory(self):
        transport = client(lambda request: httpx.Response(429, headers={'Retry-After': '120'}))
        for _ in range(2):
            with self.assertRaises(CliError) as caught:
                transport.read('GET', '/v2/cuisines')
            self.assertEqual(caught.exception.code, 'rate_limited')
        self.assertEqual(transport.requests, 1)
        self.assertEqual(transport.trace[0]['http_status'], 429)
        transport.close()

    def test_unconfirmed_filtered_slot_remains_partial_at_budget_limit(self):
        def handler(request):
            if '/v2/shops/' in request.url.path:
                return response({'shops': [SHOP]})
            if request.url.path.endswith('/reserve'):
                return httpx.Response(200, text='<input name="reservation[service_category]" value="private">')
            return response({'queried_date': '2026-12-01', 'data': {'slots': {'2026-12-01': {'1796115600': {'available': True}}}}})
        transport = client(handler, budget=3)
        result = TableCheck(transport).availability(SHOP['slug'], '2026-12-01', '2026-12-01', 2, '17:00', '21:00', seat='Private')
        self.assertEqual(result['coverage'], 'partial')
        self.assertFalse(result['days'][0]['complete'])
        self.assertEqual(result['days'][0]['offered_times'], [])
        transport.close()

    def test_unrelated_parameters_and_implicit_party_sizes_are_rejected_offline(self):
        for args in (['availability', SHOP['slug'], '--date', '2099-12-01'], ['detail', SHOP['slug'], '--near', '36,136'],
                     ['search', '--near', '36,136', '--people', '2'], ['detail', SHOP['slug'], '--no-courses', '--date', '2099-12-01']):
            result = run(args)
            self.assertEqual(result['output']['status'], 'error')
            self.assertIsNone(result['output']['usage'])

    def test_course_dates_and_money_preserve_source_conditions(self):
        def handler(request):
            return response({'shops': [SHOP]}) if '/shops/' in request.url.path else response({'menu_items': [COURSE]})
        transport = client(handler)
        result = run(['detail', SHOP['slug'], '--from', '2026-11-30', '--to', '2026-12-02', '--meal', 'dinner'],
                     create_client=lambda **_: transport)
        self.assertEqual(result['output']['status'], 'ok')
        item = result['output']['data']['courses'][0]
        self.assertEqual(item['price'], '55000.0')
        self.assertEqual(item['eligible_dates'], {'2026-11-30': False, '2026-12-01': True, '2026-12-02': True})
        self.assertIsNone(item['computed_total'])
        transport.close()

    def test_course_only_query_checks_required_seats_and_keeps_the_actual_category(self):
        shop = {**SHOP, 'tc_input_service_category': 'required', 'service_categories': [
            *SHOP['service_categories'], {'id': 'counter', 'name_translations': [{'locale': 'en', 'translation': 'Counter'}]}]}
        def handler(request):
            path = request.url.path
            if '/v2/shops/' in path:
                return response({'shops': [shop]})
            if path.endswith('/menu_items'):
                return response({'menu_items': [{**COURSE, 'service_category_ids': ['private', 'counter']}]})
            if path.endswith('/reserve'):
                return httpx.Response(200, text='<input name="reservation[service_category]" value="private">'
                    '<input name="reservation[service_category]" value="counter">'
                    '<input name="reservation[orders_attributes][2][menu_item_id]" value="'+COURSE['id']+'">'
                    '<input name="reservation[orders_attributes][2][is_group_order]" value="true">')
            if path.endswith('/timetable'):
                return response({'queried_date': '2026-12-01', 'data': {'slots': {'2026-12-01': {
                    '1796115600': {'available': request.url.params['reservation[service_category]'] == 'private'}}}}})
            return response({'status': 'success'})
        transport = client(handler)
        result = TableCheck(transport).availability(shop['slug'], '2026-12-01', '2026-12-01', 2, '17:00', '21:00', course=COURSE['id'])
        self.assertEqual(result['coverage'], 'complete')
        self.assertEqual(result['days'][0]['offered_times'], ['18:00'])
        self.assertEqual(result['days'][0]['slots'][0]['seat_category_id'], 'private')
        self.assertEqual(transport.requests, 6)
        transport.close()

    def test_search_verifies_candidates_and_stops_after_enough_available_results(self):
        shops = [{**SHOP, 'slug': name, '_id': str(index)*24} for index, name in enumerate(('first', 'second', 'third'), 1)]
        queried = []
        def handler(request):
            queried.append(request.url.path)
            if request.url.path.endswith('/shop_search'):
                return response({'shops': shops, 'meta': {'last_page': True}})
            if '/v2/shops/' in request.url.path:
                return response({'shops': [next(shop for shop in shops if request.url.path.endswith('/'+shop['slug']))]})
            if request.url.path.endswith('/menu_items'):
                return response({'menu_items': [COURSE]})
            body = json.loads(request.content)
            return response({'availability_calendar': {'type': 'success', 'time_zone': 'Asia/Tokyo',
                'data': {'2026-12-01': calendar('2026-12-01', body['shop_id'] != '1'*24)}, 'closed_dates': []}})
        transport = client(handler)
        result = TableCheck(transport).search((36.5, 136.5), 1000, [], None, None, 2, 1,
            '2026-12-01', '2026-12-01', 2, '17:00', '21:00', True, 'dinner')
        self.assertEqual([item['slug'] for item in result['items']], ['second'])
        self.assertTrue(result['limit_reached'])
        self.assertNotIn('/v2/shops/third', queried)
        self.assertEqual(transport.requests, 6)
        transport.close()

    def test_foreign_urls_and_write_routes_are_rejected_without_network(self):
        with self.assertRaises(CliError):
            slug_value('https://example.org/en/shops/sample-restaurant/reserve')
        transport = client(lambda request: self.fail('unexpected network request'))
        with self.assertRaises(CliError):
            transport.read('POST', '/v2/hub/reservations', body={})
        self.assertEqual(transport.requests, 0)
        transport.close()
