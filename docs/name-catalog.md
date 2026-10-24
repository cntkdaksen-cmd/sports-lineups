# Reviewed names and full club names

`dist/name-catalog.json` is the public name feed consumed on every site refresh. The browser falls back to its bundled catalog when GitHub is unavailable.

Approve full team names and provider aliases in `scripts/team-name-review.json` and `dist/team-ko.json`. Add established player names to `dist/player-ko.js` or `scripts/player-name-review.json` (`userOverrides`). Keep club/player identity and source evidence in the review files. Do not infer identity from surnames. Identifiable Google results may be approved directly.

The name workflow independently builds and validates the approved catalog every 15 minutes and whenever review sources change. The existing lineup workflow collects new names across every league. It uploads unreviewed names with Google and Naver search links in `name-review-queue.json`. Search evidence is automatically assessed under the Google-first rules below; inconclusive names remain queued. Approved catalog updates reach the site without a new frontend deployment.

Run locally:

```sh
node scripts/build-name-catalog.mjs
node scripts/check-player-names.mjs --inventory scripts/fixtures/player-name-inventory.json --require-reviewed
```


## Automatic verification without API keys

The name workflow runs every 15 minutes. It collects current lineup, starting-pitcher and injury names across every league (not only the major-games overview). Already translated names are skipped. The collector preloads seven days of games while the public site remains today/tomorrow only. Today/tomorrow starters and pitchers take priority over injuries and future games. Names are normalized to avoid repeated accent/punctuation lookups. Each run first checks up to 1,000 names through Wikipedia Korean language links in batches of 20. Approval requires an exact English page title, a sports biography, and a Korean language link to the same page; a nonexact title also requires the current club in its introduction. Existing manual spellings override these additions. It then attempts at most 30 unregistered names, with a ten-minute search budget, through public Google and Naver search pages. No search API secret or paid service is used.

Google search results can now approve a name immediately, without fetching a second publisher. A Korean title with the exact bilingual name and team context, or an unambiguous Google knowledge-panel title with the exact English name and team context, is sufficient. Conflicting names and missing identity context stay unapproved. The evidence URL, content hash and method `google-search-result-v1` are saved. Old pending records become eligible under this new policy without waiting out their previous retry date.

If no identifiable Google result is readable, the existing Google/Naver source fallback remains: Fallback approval requires the same Korean full name paired with the exact English full name in two independently hosted source documents, plus the current club on at least one document. Only configured sports publishers, official sports sites and Wikipedia are fetched; at least one source must be outside Wikipedia. Different spellings, ambiguous team identities, missing club context and inaccessible pages remain unapproved. This deliberately favors avoiding wrong names over maximum coverage. Existing human-reviewed spellings take priority.

The resolver does not bypass CAPTCHA, access blocks or JavaScript challenges. Both search providers are attempted; a blocked provider does not prevent two accessible independent documents from establishing the name. `scripts/player-name-search-state.json` distinguishes unreadable search responses from verified results and records retries (six hours when neither search is readable; 24 hours after inconclusive readable results). It is **not** proof that a Korean name does not exist. Public search access is unreliable; a successful scheduled run can add zero names. Full rosters for clubs without upcoming games are not imported. The seven-day preload covers players supplied by the available lineup feeds. The run report records bulk approvals, search approvals and failures; a green workflow alone is not evidence of new translations.

Approved evidence is kept in `scripts/player-name-auto-review.json`. The catalog builder merges those names beneath manual dictionaries and publishes `dist/name-catalog.json`, which the website reads on refresh. Source documents are not published in full and no source links are added to the website UI.

Team display uses the reviewed Korean full name and optional `english` full name from `scripts/team-name-review.json`. Team names do not fall back to `shortDisplayName`. Long names may wrap rather than being abbreviated.

Checks: `python3 scripts/test_resolve_player_names.py`, followed by the existing name/catalog rendering checks. Live search success must be inspected separately from offline tests.

`player-name-run-report.json` and the GitHub job summary report each run. Both-search-provider failure stops repeated search requests, but bulk language-link lookup remains independent.
