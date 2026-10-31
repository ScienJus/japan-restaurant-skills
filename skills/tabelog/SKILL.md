---
name: tabelog
description: "Find Japanese restaurants on Tabelog by area, station, or coordinates; filter by cuisine, rating, and Hyakumeiten selection; read recent reviews and check online reservation dates, party-size ranges, and time slots. Also lists area and station catalogs. Does not submit reservations."
---

# Tabelog restaurant search, reviews, and availability

Use current queries with traceable sources. Read [README.md](README.md) for setup and commands, then use `bin/tabelog` at the repository root or `python scripts/tabelog.py` inside the skill. Use command-specific `--help`; unsupported options are rejected. Keep new sources and reusable operations in CLI code rather than ad hoc HTTP commands or browser steps.

## Access and authorization

Prefer verified APIs, then coded HTML parsers, then a separately implemented headless adapter if necessary. Desktop-browser/CUA use requires explicit confirmation for the specific purpose. The current CLI needs no browser or personal account and cannot submit reservations.

If a future feature needs a user identity, explain the platform/account, purpose, actions, credentials/session data involved, and account/privacy risks. Obtain explicit consent for that scope before accessing, importing, reusing, or transmitting credentials or authenticated sessions. A restaurant-search request is not account authorization. Keep credentials/session data out of logs, reports, commits, and shared captures. Routine anonymous queries need no account confirmation. See the [account-risk notice](README.md#responsible-use-and-account-risk).

Run requests serially with default same-site delays. Separate processes share no pacing/cooldown state. Stop on denials, challenges, or rate limits and honor `retry_not_before`; do not rotate clients, identities, or fingerprints to continue. See the [request policy](references/access.md#request-policy).

## Choose the workflow

- **Location and catalogs:** use `suggest`, `station`, `geocode`, `areas`, or `stations`. Bare `areas` lists prefectures offline. Verify geocode candidates by name, city/address, and type before using their coordinates. Do not assume the first result is correct or access device location implicitly. Read [catalog.md](references/catalog.md) for directory scope.
- **Search:** use `--area`, `--station`, or `--near LAT,LON`. Station/coordinate searches default to 1 km; area searches retain area scope. Add only requested filters. Unspecified budget meals may match either meal; report which. An opening time without a date returns ordinary weekdays, not a visit-date guarantee. Return up to five results in rating order by default, stopping once enough match. Read [search.md](references/search.md).
- **Hyakumeiten:** add only `--hyakumeiten`, combined with ordinary `--cuisine` when needed. The CLI includes all current categories automatically. Search has no category/year options; do not infer each restaurant's award edition from query categories. Details retain observed badges; `awards` provides individual verification.
- **Details and courses:** use `detail`; listed courses do not require date/party inventory queries or prove availability.
- **Reviews:** use `reviews`, optionally `--meal lunch|dinner` and `--full`, or `review-read` for one review. State the visit-date basis, window, sample size, and precision. Distinguish each visit's meal/date and keep old or uncertain passages separate. Read [reviews.md](references/reviews.md).
- **Availability:** use bare `calendar RESTAURANT` for a one-read date overview; add dates for party-size hints. `slots`/`availability` require dates; omit `--people` to verify times for returned selectable sizes, or specify known people to avoid extra checks. Only apply requested meal/time filters; omitted `--time` uses the upstream anchor. Compose `search` with booking commands using confirmed IDs/URLs. Read [availability.md](references/availability.md). Do not fill forms, hold seats, book, or pay.

## Interpret and present results

Inspect `status`, `error`, coverage, `unverified`, and `trace` before answering. Success does not imply exhaustive coverage. Missing or inaccessible data remains unknown; do not silently relax filters, expand scope, or treat errors as no results.

Use Asia/Tokyo dates/times and respond in the user's language, retaining Japanese restaurant names. Link restaurants and sources; state location/radius, filters, query time, and coverage. Compare only supported facts such as overall rating, cuisines, distance, meal budgets, hours, and observed awards. Do not substitute sample review scores for overall ratings, straight-line distance for walking distance, or published hours for confirmed seats.

Explain execution as actual CLI commands, underlying sources/formats, external dependencies, and measured `usage`. See [costs.md](references/costs.md). Do not rerun queries just to explain them or invent unmeasured costs. For recent-review questions, summarize the actual sample rather than returning raw JSON alone.
