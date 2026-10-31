---
name: tablecheck
description: "Find restaurants on TableCheck, read courses and their conditions, and check dates and time slots for a party size, optionally constrained by a course or seat category. Anonymous queries only; does not submit reservations."
---

# TableCheck discovery, courses and availability

Use `bin/tablecheck` from the repository root. Inside a standalone skill installation, use `python scripts/tablecheck.py`. Use command-specific `--help`; unsupported parameters are rejected. All queries are anonymous HTTP reads; no API key, account, Node.js or browser is required.

## Setup

Reuse the repository's Python environment and run `bin/tablecheck doctor` without network requests. For a standalone installation, create a Python 3.10+ virtual environment (3.12+ recommended) and install `scripts/requirements.txt`, then run `python scripts/tablecheck.py doctor`. HTTPX and Beautiful Soup are the runtime dependencies. The skill includes its MIT license.

## Commands

| Command | Purpose and main options |
| --- | --- |
| `suggest QUERY` | Restaurant slugs and native city/area suggestions, including type, parent area and center coordinates |
| `search --near LAT,LON` or `search --area PLACE` | Restaurants in distance order; `--radius-m` (default 1000 for coordinates, 10000 for an area), repeatable `--cuisine`, `--budget-min`, `--budget-max`, `--pages` (default 2), `--limit` (default 5) |
| `detail RESTAURANT` | Restaurant details, seat categories and courses; `--no-courses` skips menus |
| `courses RESTAURANT` | Courses and their published conditions; optional `--date` or `--from/--to`, `--meal`, `--course ID` |
| `calendar RESTAURANT` | Available dates and time counts; same scope/options as `availability`, without the full time list |
| `slots RESTAURANT --date YYYY-MM-DD` | One day's offered times |
| `availability RESTAURANT` | Dates and offered times for `--date` or `--from/--to` (1–31 days) |
| `cuisines` | Native cuisine keys and translated labels |
| `doctor` / `usage RESULT_JSON...` | Offline dependency checks / summed recorded query costs |
| `source READ_ENDPOINT_PATH` | Bounded diagnostics for allowed read endpoints; optional JSON `--params` or `--body` |

`RESTAURANT` accepts a public TableCheck restaurant URL or slug. `detail` accepts the same course filters as `courses`; its default menu window is today through 30 days later. Prices remain exact source strings, with currency and tax/service flags. Published course eligibility and a menu's `availability_status` do not prove a bookable time slot. Fine print can qualify a headline price; do not invent a final total or free cancellation.

Inventory queries require `--people` (adults). Child and baby counts are zero; this version does not claim support for mixed-age parties. Party-size enumeration is not available. Use `--meal lunch` (11:00–15:00 local), `--meal dinner` (17:00–21:00), `--after/--before`, or one exact `--time`. Without time filters the CLI checks 00:00–23:59 using multiple anchors. These meal windows are query conventions, not restaurant opening hours. Elapsed same-day times are omitted. Do not silently choose a meal for the user.

`--area` resolves a native TableCheck location suggestion and searches around its center; this is a radius, not a city's complete administrative boundary. Inspect the resolved name, type, parent area, center and radius. Ambiguous names require a more specific name or explicit coordinates; do not silently substitute another city.

For a single date plus `--people`, `search` asks the native search endpoint for the day's indexed availability across restaurants. Omitted time returns the day's indexed times, including quarter-hour starts where exposed. `--meal`, `--after/--before`, or exact `--time` filters that list locally. Users can choose `--time` from returned `offered_times`; they need not guess a value or select an ID. Each result says `verification=search_index_only` and retains source index timestamps. These are discovery hints, not course/seat confirmation; use `availability` on a selected restaurant for a separate check. Do not equate the upstream catalog's record count with the number of available restaurants.

Multi-day `search --from/--to` checks each candidate's venue calendar instead. `--with-courses` adds menus only for retained results and reuses shop IDs/time zones already returned by search. Search budgets are **venue dinner averages**, not lunch budgets or all-in course prices. Repeated cuisine filters require all requested keys. Search stops once enough matches are found. Do not add unsupported Tabelog rating or Hyakumeiten filters.

Add `--course ID` and/or `--seat CATEGORY_ID_OR_EXACT_NAME` to inventory queries when requested. Read IDs and seat names from the same restaurant's details first. Filtered inventory currently requires a public v1 booking form. The CLI reads the actual menu index and category from that form, batches dates through its timetable endpoint, then confirms positive slots using a second GET. If a course query omits a seat but the form requires one, it checks each applicable seat category separately and preserves category IDs on confirmed slots; this increases requests. A v2 venue with these filters returns an explicit unsupported-scope error, rather than silently checking venue-wide inventory. Booking links are for human handoff; the returned course/seat evidence remains separate from URL prefills.

An API-required seat flag with no API categories is checked against the public form. If the course has no seat restrictions and the form exposes no seat selector, course-only queries can proceed with `seat_linked=false`; the seat type remains unverified. An explicit `--seat` is never dropped.

```bash
bin/tablecheck suggest 海老亭別館
bin/tablecheck search --area 金沢 --radius-m 10000 --date 2026-12-02 --people 2 --limit 5
bin/tablecheck detail ebiteibekkan --from 2026-12-01 --to 2026-12-30
bin/tablecheck availability ebiteibekkan --from 2026-12-01 --to 2026-12-30 --people 2 --meal dinner
bin/tablecheck availability ebiteibekkan --date 2026-12-02 --people 2 --meal dinner --course COURSE_ID --seat Private
bin/tablecheck search --near 36.5781,136.6477 --radius-m 1000 --limit 5 --date 2026-12-02 --people 2 --meal lunch --with-courses
```

Replace example dates with current trip dates and `COURSE_ID` with an observed ID.

## Request policy and interpretation

Use the CLI for all requests. It permits only known consumer read routes, including the two read-only POST queries for menus and calendars. Do not fill forms, hold seats, create reservations, join waitlists or pay. Never import login cookies, browser profiles, credentials or authenticated sessions. Any future account workflow needs separate scoped consent before identity access; restaurant queries do not grant it. Desktop-browser/CUA use requires explicit confirmation for that specific use.

Requests are serial, with default 1–2.5 second delays across both TableCheck hosts, per-command memory caching, 15-second timeouts, an 8 MiB response limit and a default 20-attempt budget. Shared flags are `--timeout`, `--max-requests` (maximum 80), `--delay-min-ms` and `--delay-max-ms`. Stop on denials, challenges, throttling or service-unavailable responses; honor `retry_not_before`. Do not switch clients or identities to continue. Separate commands share no cooldown state and must be coordinated.

Inspect `status`, `data.coverage`, per-day `complete`, `errors`, and `trace`. Missing dates, unrecognized booleans, failed confirmations and exhausted budgets stay unknown/partial, not sold out. Native calendar responses cover a source time grid around an anchor, not every possible start time; `complete` describes the required source responses, not exhaustive restaurant inventory. Single-day search can expose additional quarter-hour starts. The CLI reuses multi-day coverage and does not default to daily scanning. An unavailable result does not distinguish every unreleased-inventory case. Results are timestamped observations, never reservation guarantees.

Respond in the user's language and retain Japanese names. Report the actual commands, dates, people/time/course/seat scope, restaurant links, coverage and measured `usage`. Times use the venue's time zone (Japan venues: Asia/Tokyo). Source diagnostics redact common form tokens and Google API keys, but are not a general personal-data sanitizer; keep captures out of commits and shared reports.

## Query costs

Counts assume known slugs, no failures and no cache hits. N is the number of missing date/time windows; W is filtered timetable windows and S is positive slots needing confirmation.

| Operation | HTTP reads |
| --- | --- |
| Name suggestions / one search page / cuisine catalog | 1 each |
| Area name resolution | +1 native autocomplete read |
| Details without / with menus | 1 / 2 |
| Courses | 2 |
| Venue calendar/slots/availability | 1 venue lookup + N native calendar reads; a covered month at one meal can need only 2 total |
| Course/seat inventory | Venue + public form, plus menus when a course is selected, then W + S; the request budget bounds the total |
| Single-date search with people | Search pages; no per-restaurant calendar reads. Each retained restaurant's menus add 1 read when requested |
| Multi-day search with people | Search pages + each checked candidate's inventory; menus only for retained results when requested |
| Doctor / usage | 0 |

The native calendar allows at most one follow-up date window per time anchor; remaining missing dates stay partial. Filtered timetables reuse every explicitly returned date. `usage` records request starts, decoded response bytes, elapsed time, pacing, cache hits and HTTPX version. It does not measure wire bytes, CPU, memory, model tokens or money. Save JSON outputs and aggregate them offline without re-querying.

## Sources and acknowledgments

- [TableCheck official API documentation](https://tablecheck.atlassian.net/wiki/spaces/API/pages/44630975/Getting+Started): the partner API requires approved credentials and is separate from this consumer-interface implementation.
- [Printing Press TableCheck CLI](https://github.com/mvanhorn/printing-press-library/tree/main/library/food-and-dining/tablecheck): consumer search, menus and calendar API shapes and explicit inventory scopes.
- [dine-mcp-server](https://github.com/benjamin-di/dine-mcp-server/blob/main/src/dine_mcp/providers/tablecheck.py): time-window coverage and bounded multi-day calendar queries.
- [tc-mcp](https://github.com/nbw/tc-mcp): autocomplete, cuisine and discovery endpoint research.
- [tablecheck-watcher](https://github.com/Hyu-waseda/tablecheck-watcher): seat-category timetable research.

These are research references, not installed runtime tools. This CLI uses Python HTTPX and Beautiful Soup directly. Consumer endpoints are undocumented and can change. Live anonymous checks on 2026-10-31 covered Kanazawa nearby discovery, 海老亭別館 details/courses and December venue/course/seat inventory; historical examples do not promise current availability.

## Responsible use and license

Provided for learning, research and reference. Follow applicable laws, platform terms and privacy/data-use requirements; do not bulk harvest, disrupt services or bypass access restrictions. This project is independent of TableCheck and grants no rights to third-party services or data. Anonymous operation does not imply platform approval. For any future account workflow, obtain the scoped consent described above; users decide whether to accept account and privacy risks.

The [MIT License](LICENSE) is included for standalone redistribution, with its warranty and liability disclaimers. Results and continued access are not guaranteed; verify important restaurant and booking conditions with the platform or restaurant. This notice does not add restrictions to the MIT software license.
