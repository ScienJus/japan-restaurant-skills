# Search, coordinates, and filters

## Location

- Use `search --area`, `--station`, or `--near LAT,LON`. Area searches retain area scope; station/coordinate searches default to a 1,000-meter radius. `--station` is exclusive with the other two; `--near` may include an explicit fallback `--area`.
- For hotels, landmarks, or addresses, use `geocode` and verify candidate name, city/address, and type before reusing `near`. Photon is the default; GSI is available for Japanese addresses. A provider representative point may be a centroid rather than an entrance.
- Coordinates are WGS84 latitude,longitude. GeoJSON input arrays are longitude-first; CLI output is latitude-first. Do not silently swap or assume an unknown datum.
- Station centers use a unique exact-name GSI point after Tabelog identity resolution. Restaurant coordinates come from map records or Restaurant JSON-LD, with their own `coordinate_source`.
- Map results cover a rectangle. The CLI deduplicates and applies the circular radius using unrounded great-circle distance. Totals describe the rectangle, not the circle; distance is not walking distance. Missing coordinates remain unverified. Pole/antimeridian-crossing bounds are unsupported.

## Filters and coverage

- Search requests rating order (`SrtT=rt`) and stops once `--limit` matches are found. Defaults: 5 results and at most 2 pages; caps: 50 results and 10 pages. Inspect `meta.stop_reason`, coverage, and unverified candidates. Limited pages do not establish exhaustive results.
- Use the overall Tabelog rating, not individual review scores. Unknown ratings cannot satisfy a threshold. List/detail differences may reflect different snapshots.
- Repeated `--cuisine` values mean OR; different filter dimensions mean AND. Search retains list cuisine classifications for filtering; translated detail cuisines are kept separately as `localized_cuisines`. Use source classifications, not a dish mentioned in review text. Japanese labels such as 寿司, 焼肉, 焼き鳥, and 居酒屋 are accepted.
- `--hyakumeiten` automatically loads all current native category IDs and sends them together. Use `--cuisine` for cuisine preferences. Search has no category/year options. The catalog exposes no edition/year or exact per-restaurant winning category; details retain observed badges, and `awards` provides individual verification. Tabelog Award and Hyakumeiten are distinct.
- Budgets are JPY per person from list bands. `--budget-meal` inherits `--meal`; if both are omitted, either lunch or dinner may match. `budget_filter.matching_meals` identifies confirmed meals and `checks` retains both bands. A whole band must fit; missing/crossing bands stay unverified unless another meal matches. Do not substitute course prices or reviewer spending.
- `--meal` requires regular-hour overlap with lunch 11:00–14:00 or dinner 17:00–21:00 on at least one weekday. It does not confirm a meal menu, a specific date, or seats.
- `--open-date` checks published rules for a date; `--open-at` checks a time; `--open-until` requires `--open-at` and the whole stay. Earlier end times mean next day. Breaks are not bridged, and closing time disallows entry.
- Without `--open-date`, time checks return ordinary `matching_weekdays`, `unknown_weekdays`, and `weekday_results` using 0=Sunday through 6=Saturday. No visit date or current weekday is assumed. Holiday/adjacent-holiday rows remain in `special_rules`; their applicability requires a date. Known matching weekdays can coexist with unknown weekdays.
- Date checks use weekday/holiday/adjacent-day and overnight rules. Irregular closures, unparsed exceptions, reservation conditions, and uncertain last orders remain unknown. `matches_regular_hours` is not a guarantee of actual opening or availability.

Do not expand radius, relax filters, or substitute historical awards to fill a list without agreement. Return source links, query time, filters, scope, and unknowns. Keep query categories separate from observed award records.
