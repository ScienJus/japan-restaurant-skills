# Japan Restaurant Skills

Agent skills and CLI tools for finding Japanese restaurants, reading reviews, and checking online reservation dates and times. Tabelog is the main integration; TableCheck supports anonymous discovery, courses and availability. OMAKASE may be added as a separate skill in the future. Current operations are read-only and do not submit reservations.

Read the [responsible-use and account-risk notice](#responsible-use-and-account-risk) before making queries or authorizing access to an account.

## Use with an agent

Give an agent this repository URL or a local checkout, followed by a request such as:

> Use https://github.com/ScienJus/japan-restaurant-skills to find up to five lunch restaurants within 1 km of Kanazawa Station with a Tabelog rating of at least 3.5. Read AGENTS.md and the Tabelog skill, set up the CLI if needed, and report results with sources, commands, dependencies, and measured request costs.

The agent needs terminal access, Python 3.10+, and outbound network access. It can clone or download the repository and use the CLI directly; global skill installation is optional. Ordinary queries require no API key, account, or browser. A chat interface without code execution cannot run the CLI from a URL alone.

To install just the Tabelog skill in Codex, ask:

> Use $skill-installer to install https://github.com/ScienJus/japan-restaurant-skills/tree/main/skills/tabelog.

Then follow the [standalone setup](skills/tabelog/README.md#installation) to install its Python dependencies.

## Available skills

| Skill | Status | Capabilities |
| --- | --- | --- |
| [Tabelog](skills/tabelog/SKILL.md) | Available; main integration | Restaurant search, details, courses, reviews, awards, and online reservation availability |
| [TableCheck](skills/tablecheck/SKILL.md) | Available; first version | Restaurant discovery, courses, multi-day availability, and course/seat combinations on public v1 booking forms |

- [Tabelog guide and acknowledgments](skills/tabelog/README.md): installation, commands, examples, and limitations.
- [Skill entry point](skills/tabelog/SKILL.md): agent workflows, evidence, and access rules.
- [Query costs](skills/tabelog/references/costs.md): request-count formulas, dependencies, and measurement scope.
- [TableCheck guide](skills/tablecheck/SKILL.md): commands, anonymous request policy, costs and acknowledgments. Install the standalone skill from `skills/tablecheck` using the same skill-installer flow if needed.

## Local setup

Requires Python 3.10+ (3.12+ recommended), HTTPX, Beautiful Soup, and jpholiday. No Node.js or browser dependency.

Run from the repository root. Check `python3 --version` first; if it is older than 3.10, use a suitable interpreter such as `python3.12` in the first command instead. See the [Tabelog installation guide](skills/tabelog/README.md#installation) for interpreter installation and standalone skill use.

```bash
git clone https://github.com/ScienJus/japan-restaurant-skills.git
cd japan-restaurant-skills
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
bin/tabelog doctor
bin/tablecheck doctor
bin/tabelog search --station 金沢駅 --radius-m 1000 --min-rating 3.5 --meal lunch
bin/tablecheck suggest 海老亭別館
```

## Development

Offline validation:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python -m pip check
.venv/bin/python scripts/check_submission.py
```

Repository documentation and skill metadata are maintained in English only. Japanese names, addresses, cuisine labels, and source fixtures retain their original wording. Agents respond in the user's language.

`research/`, virtual environments, caches, and build outputs are ignored. Tests use the necessary samples in `tests/fixtures/` and do not require development captures.

GitHub Actions runs the offline checks on pushes and pull requests. It does not query restaurant platforms.

## Responsible use and account risk

This project is provided for learning, research, and reference. Users are responsible for checking and following applicable laws, platform terms, published crawling rules, and privacy and intellectual-property requirements. It does not authorize access to restricted content or use of third-party data beyond the rights granted by its owners. Do not use it for bulk harvesting, disruptive traffic, or bypassing access restrictions. The project is independent of, and is not endorsed by, the platforms it queries.

The current CLI is designed to reduce unnecessary requests and service load through serial requests, default 1–2.5-second same-site delays, per-command caching and request limits, early stopping once enough restaurants match, and calendar screening before candidate time-slot queries. It stops further reads on access denials, challenges, rate limits, and service-unavailable responses. These measures reduce traffic; they do not guarantee zero impact, continued access, or protection from blocking. Limits apply within each command, so users and agents must also coordinate separate commands and respect server cooldowns. See the [request policy](skills/tabelog/references/access.md#request-policy).

All currently implemented CLI queries work without personal account credentials and do not import a user's login cookies or browser profile. If a future feature or browser-assisted workflow requires a user identity, the tool or agent must first explain the platform and account involved, the purpose and actions, which credentials or session data would be used, and the account/privacy risks. It must obtain the user's explicit consent for that scope **before accessing, importing, reusing, or transmitting credentials, login cookies, tokens, or an authenticated session**. General permission to search for restaurants does not authorize account access. Credentials and session data must not be included in logs, reports, commits, or shared captures.

Users decide whether to authorize account-based access and accept the associated risks, including additional verification, account restrictions or suspension, and exposure of account or personal data. Consent does not guarantee that a platform permits the activity or that an account will be unaffected. The software and returned information are provided as is; no guarantee is made about accuracy, completeness, availability, or suitability for a particular purpose. Verify important restaurant and booking information with the platform or restaurant. To the extent permitted by applicable law, authors and contributors disclaim warranties and liability for losses arising from use, including account consequences, as set out in the [MIT License](LICENSE).

This notice describes the project's intended use and operating rules; it does not add restrictions to the MIT software license or grant rights to third-party services or data.

## License

This project is licensed under the [MIT License](LICENSE). Upstream parser attribution and its MIT notice are retained under [licenses/](skills/tabelog/scripts/client/licenses/tabelog-cli.txt), with provenance included in the wheel.
