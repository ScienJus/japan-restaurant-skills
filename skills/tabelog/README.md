# Tabelog restaurant search

Find Japanese restaurants, read details and reviews, and check online reservation availability through one Python CLI. Queries are anonymous and read-only; no API key, account login, Node.js, or browser is required. The CLI does not submit reservations.

## Installation


Requires **Python 3.10+; 3.12+ recommended**. Do not assume a suitable interpreter is preinstalled. Use the [official Python installer](https://www.python.org/downloads/) or an existing package manager.

Runtime and installation checks were performed on macOS with Python 3.12. Python 3.10 syntax was checked; Python 3.10 and Windows have not been tested on actual hosts.

From the repository root on macOS/Linux:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
bin/tabelog doctor
bin/tabelog --help
```

`requirements.lock` pins the validated runtime dependencies. `python -m pip install .` is also supported and resolves the compatible ranges in `pyproject.toml`. Existing uv users can run `uv tool install . --python 3.12`; uv is optional.

On Windows, from the repository root:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock
.venv\Scripts\python.exe -m pip install --no-deps -e .
.venv\Scripts\tabelog.exe doctor
```

The installed command is `tabelog`. Examples use the source launcher `bin/tabelog`, which selects `TABELOG_PYTHON`, then the repository's `.venv/bin/python`, then `python3` on PATH.

Use `bin/tabelog --help` for the command list and `bin/tabelog search --help` (or another command) for its options. Request controls (`--timeout`, `--max-requests`, `--delay-min-ms`, and `--delay-max-ms`) are shared and may appear before or after the command. Other options belong to their specific command; unsupported options are rejected before requests. For example, search uses `--open-date` for opening-hours checks, while `--date` and `--people` belong to booking queries.

For a separately copied skill directory, install `scripts/requirements.txt` in a virtual environment and run `python scripts/tabelog.py --help`. The repository launcher is not required.

## Commands

Run `bin/tabelog --help` for the list or `bin/tabelog COMMAND --help` for that command's options. `RESTAURANT` below means a Tabelog URL or numeric ID.

| Command | Purpose |
| --- | --- |
| `suggest QUERY` | Area, station, cuisine, and restaurant suggestions |
| `station STATION` | Resolve station identity and coordinates |
| `geocode PLACE` | Place/address coordinates; `--provider photon` (default) or `gsi` |
| `areas` | Offline prefecture directory; add `--prefecture CODE_OR_NAME`, `--parent AREA1_ID`, or `--city CITY_NAME` to descend |
| `stations --area AREA2_ID` | Stations in a Tabelog search area |
| `search` | Restaurant search by `--area`, `--station`, or `--near LAT,LON` |
| `detail RESTAURANT` | Details, hours, budgets, courses, and observed award records |
| `awards RESTAURANT` | Individual badge verification; optional `--year` and one `--category` |
| `reviews RESTAURANT` | Visit-date reviews; `--meal`, `--since`, `--until`, and optional `--full` |
| `review-read REVIEW_URL` | A full review with separate visit records |
| `channel RESTAURANT` | Evidence for a Tabelog online booking channel |
| `calendar RESTAURANT` | One-read date overview; add `--date DATE` or `--from DATE --to DATE` for party-size hints |
| `slots RESTAURANT --date DATE [--people N]` | Time slots for one or all returned selectable party sizes; optional `--time` |
| `availability RESTAURANT --date DATE [--people N]` | Verified availability; use `--from DATE --to DATE` for a range |
| `hyakumeiten-categories` | Optional native catalog diagnostics |
| `source HTTPS_URL` | Diagnostic source; optional `--prime HTTPS_URL` |
| `doctor` | Offline dependency check |
| `usage RESULT_JSON ...` | Offline cost aggregation |

## Examples

```bash
# Lunch within 1 km of Kanazawa Station, rated at least 3.5.
bin/tabelog search --station 金沢駅 --radius-m 1000 --min-rating 3.5 --meal lunch

# Hyakumeiten sushi restaurants in an area.
bin/tabelog search --area 銀座 --hyakumeiten --cuisine 寿司

# List lunch budget per person.
bin/tabelog search --station 金沢駅 --meal lunch --budget-max 5000

# Either lunch or dinner list budget fits; results identify matching meals.
bin/tabelog search --station 金沢駅 --budget-max 5000

# Regular weekdays open at 12:30, without assuming a visit date.
bin/tabelog search --station 金沢駅 --open-at 12:30

# Confirm a hotel's location before reusing a geocode candidate's near value.
bin/tabelog geocode 'Hyatt Centric Kanazawa'

# Recent dinner reviews and full text.
bin/tabelog reviews 16010357 --meal dinner --full

# Replace the dates with your visit window; check dinner availability for two.
bin/tabelog availability 16010357 --from 2026-12-01 --to 2026-12-31 \
  --people 2 --after 17:00 --before 23:59

# Discover date and party-size hints without time-slot queries.
bin/tabelog calendar 16010357 --from 2026-12-01 --to 2026-12-04

# Read only the upstream date overview, without per-date expansion.
bin/tabelog calendar 16010357

# Verify time-specific party-size ranges for one date.
bin/tabelog slots 17013984 --date 2026-12-01
```

## Behavior and limits

- Search uses rating order, returns up to 5 matches by default, and stops early. `--pages` caps reads (default 2, maximum 10); `--limit` accepts 1–50. Limited pages do not establish exhaustive coverage.
- Station/coordinate searches default to a 1,000-meter straight-line radius. Area scope and municipal boundaries are different; catalogs are Tabelog search options, not an administrative census.
- Repeat `--cuisine` for OR; distinct filter dimensions use AND. `--hyakumeiten` includes all current native categories automatically and takes no category/year search options.
- Budgets use full list bands in JPY per person. `--budget-meal` inherits `--meal`; if both are omitted, either lunch or dinner may match and `matching_meals` identifies which. Missing/crossing bands remain unverified unless another meal is confirmed to match.
- `--meal` checks regular-hour overlap. With `--open-date`, opening checks use that date's published rules. `--open-at` without a date returns matching ordinary weekdays; holiday exceptions remain separate. `--open-until` requires `--open-at` and checks the whole stay. Temporary changes and uncertain conditions remain unverified.
- Dates/times use Asia/Tokyo. Reviews filter visit dates, not publication dates, and preserve month-only uncertainty. With `--full`, inspect each passage's meal and date window.
- Booking commands accept optional `--people` (1–99); explicit calendar/availability windows are at most 31 days. `calendar` without dates reads only the upstream overview, with no party-size queries. With dates it adds one native party-size read per candidate date. `--people` marks the requested size's hint; the overview is not party-specific. It never queries time slots.
- `--time` is an optional slot-search anchor; omitting it uses the upstream default. Use `--after`/`--before` on `availability` to filter returned times.
- `slots`/`availability` without `--people` verify each returned selectable size, so they can cost more than a fixed-party query. Results preserve disjoint ranges, unknowns, and per-time ranges; a date-wide range does not mean every time supports every size. Request limits still apply. A channel, course listing, or calendar hint does not establish seats for a particular meal/course.
- Frontend endpoints have no public compatibility guarantee. Restaurant data and inventory are snapshots; verify important details with the platform or restaurant.

## Results and request costs

Commands emit JSON except help. Exit codes are 0 for `status=ok`, 3 for `status=partial` with top-level `errors`, and 1 for `status=error` with an `error`. Request failures remain partial even after a successful fallback. Missing required evidence and parsing failures are reported; failed course reads use `courses.items=null`, not an empty array. Normal page/result caps use `coverage=limited`. Inspect `data`, coverage, `unverified`, `usage`, and `trace`; successful execution does not imply exhaustive results or every optional field was published.

`detail.practical_info` groups `reservation`, `payment`, `children` and `links`, retaining source wording and URLs alongside the original `info`. Recognized reservation headlines and standalone payment flags are normalized; missing or ambiguous values stay null. Read all evidence, including qualifiers and remarks. Card rejection does not establish cash-only payment. Listed booking entries are not slot checks, websites are not verified booking channels, and child policies are not mixed-age inventory checks. These fields add no requests and do not follow external links.

Requests are serial with default 1–2.5-second same-site gaps. Search stops once enough matches are found; Hyakumeiten adds one catalog read, and range availability uses one calendar read plus candidate-date checks. `usage` reports actual request starts, time, response-body bytes, and dependencies. See [costs](references/costs.md) for formulas and measurement scope.

## Agent references

Start with [SKILL.md](SKILL.md). Read only the relevant reference:

- [Search](references/search.md): location, distance, filters, and coverage.
- [Reviews](references/reviews.md): visit dates, meals, and sample interpretation.
- [Availability](references/availability.md): calendar states and inventory evidence.
- [Catalogs](references/catalog.md): area, city, and station scopes.
- [Sources and request policy](references/access.md): transport and stopping rules.
- [Costs](references/costs.md): dependencies and request accounting.

## Responsible use and account risk


This skill is provided for learning, research, and reference. Follow applicable laws, platform terms, published crawling rules, and privacy and intellectual-property requirements. Do not use it for bulk harvesting, disruptive traffic, or bypassing access restrictions. Serial requests, pacing, per-command caching and request limits, early search stopping, and calendar screening are designed to reduce unnecessary traffic; they do not guarantee zero service impact or protection from blocking. Coordinate separate commands as described in the [request policy](references/access.md#request-policy).

All current CLI queries work without personal account credentials and do not import login cookies or browser profiles. Any future account-based feature or browser-assisted workflow must explain the platform/account, purpose, actions, credentials or session data involved, and account/privacy risks, and obtain explicit consent for that scope before accessing or using the identity. General restaurant-search permission is not account authorization. Do not include credentials or session data in logs, reports, commits, or shared captures.

Users choose whether to authorize account-based access and accept associated risks, including additional verification, account restrictions or suspension, and exposure of personal data. Authorization does not guarantee platform permission or account safety. Software and results are provided as is, without guarantees of accuracy, completeness, availability, or suitability. Verify important information with the platform or restaurant. To the extent permitted by applicable law, the MIT License's warranty and liability disclaimers apply, including to account-related losses. This notice does not add restrictions to the MIT software license or grant rights to third-party services or data.

## References and acknowledgments

- [krisamin/tabelog-cli](https://github.com/krisamin/tabelog-cli/tree/0dd2b3763c102aa5d129962632fb534cab831e69): endpoint and parser references. Rewritten Python parsing retains the upstream [MIT notice](scripts/tabelog_client/licenses/tabelog-cli.txt) and [provenance](scripts/tabelog_client/licenses/tabelog-cli.provenance.json), also included in the wheel.
- [narumiruna/gurume](https://github.com/narumiruna/gurume/tree/b72909ecc7e347b55d22386809f7dbc3b9c2066a): map XML, area catalogs, and suggestion research.
- [hnaohiro/tabelog-crawler](https://github.com/hnaohiro/tabelog-crawler) and [tma15/python-tabelog](https://github.com/tma15/python-tabelog): additional research references.
- [HTTPX](https://www.python-httpx.org/), [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/), and [jpholiday](https://github.com/Lalcs/jpholiday): runtime libraries.
- [GSI](https://maps.gsi.go.jp/) and [Photon](https://github.com/komoot/photon): geocoding sources. Photon uses [OpenStreetMap data](https://www.openstreetmap.org/copyright); attribution is retained in results.

## License

Part of Japan Restaurant Skills, licensed under the [MIT License](LICENSE), included here for standalone skill installation. Retain the project and upstream notices when redistributing code or skills. This project is not affiliated with Tabelog.
