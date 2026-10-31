# Agent entry point

This repository contains platform-specific skills and CLI tools for Japanese restaurant discovery and reservation availability. Tabelog is the main integration. TableCheck supports anonymous discovery, courses and availability, including course/seat combinations on public v1 booking forms. OMAKASE is a future candidate; do not claim support for it yet.

For a restaurant query:

1. Read [skills/tabelog/SKILL.md](skills/tabelog/SKILL.md) or [skills/tablecheck/SKILL.md](skills/tablecheck/SKILL.md), according to the requested platform, and the relevant references it links to.
2. Follow the [root README setup](README.md#local-setup) from the repository root. Reuse an existing working environment; run the selected CLI's `doctor` to check dependencies without making network requests.
3. Use `bin/tabelog` or `bin/tablecheck` for supported operations. Follow the skill's request policy and report sources, unknowns, CLI commands, external dependencies, and measured usage. Respond in the user's language.

Current queries need Python and outbound network access, with no API key, login, Node.js, or browser requirement. Desktop-browser/Computer Use actions require explicit confirmation for the specific use. The CLI does not submit reservations.

Follow the [responsible-use and account-risk notice](README.md#responsible-use-and-account-risk). Before any account-based workflow, explain the platform/account, purpose, actions, credentials or session data involved, and account/privacy risks; obtain explicit consent for that scope before accessing or using the identity. A restaurant-search request is not account authorization. Do not silently reuse a logged-in browser, import login cookies, or include credentials/session data in logs, reports, or commits. Routine anonymous queries need no account confirmation.

Keep each platform's instructions and implementation in its own `skills/<platform>/` directory when adding integrations. Keep root documentation focused on discovery, setup, and routing; add shared abstractions only when implementations actually need them. Documentation is maintained in English; preserve Japanese source names and labels.
