# Reviewed names and full club names

`dist/name-catalog.json` is the public name feed consumed on every site refresh. The browser falls back to its bundled catalog when GitHub is unavailable.

Approve full team names and provider aliases in `scripts/team-name-review.json` and `dist/team-ko.json`. Add established player names to `dist/player-ko.js` or `scripts/player-name-review.json` (`userOverrides`). Keep club/player identity and source evidence in the review files. Do not infer identity from surnames or publish unverified search snippets.

The name workflow independently builds and validates the approved catalog every 15 minutes and whenever review sources change. The existing lineup workflow collects new names across every league. It uploads unreviewed names with Google and Naver search links in `name-review-queue.json`. Search evidence is automatically assessed under the independent-source rules below; inconclusive names remain queued. Approved catalog updates reach the site without a new frontend deployment.

Run locally:

```sh
node scripts/build-name-catalog.mjs
node scripts/check-player-names.mjs --inventory scripts/fixtures/player-name-inventory.json --require-reviewed
```


## Automatic verification without API keys

The name workflow runs every 15 minutes. It collects current lineup, starting-pitcher and injury names across every league (not only the major-games overview). Already translated names are skipped. Each run attempts at most five unregistered names through public Google and Naver search pages. No search API secret or paid service is used.

Search titles are candidates, never sufficient evidence. Automatic approval requires the same Korean full name paired with the exact English full name in two independently hosted source documents, plus the current club on at least one document. Only configured sports publishers, official sports sites and Wikipedia are fetched; at least one source must be outside Wikipedia. Different spellings, ambiguous team identities, missing club context and inaccessible pages remain unapproved. This deliberately favors avoiding wrong names over maximum coverage. Existing human-reviewed spellings take priority.

The resolver does not bypass CAPTCHA, access blocks or JavaScript challenges. Both search providers are attempted; a blocked provider does not prevent two accessible independent documents from establishing the name. `scripts/player-name-search-state.json` distinguishes unreadable search responses from verified results and records retries (six hours when neither search is readable; seven days after inconclusive readable results). It is **not** proof that a Korean name does not exist. Public search access is unreliable; a successful scheduled run can add zero names. Broad Korean roster imports would be a separate way to improve coverage without repeated searches.

Approved evidence is kept in `scripts/player-name-auto-review.json`. The catalog builder merges those names beneath manual dictionaries and publishes `dist/name-catalog.json`, which the website reads on refresh. Source documents are not published in full and no source links are added to the website UI.

Team display uses the reviewed Korean full name and optional `english` full name from `scripts/team-name-review.json`. Team names do not fall back to `shortDisplayName`. Long names may wrap rather than being abbreviated.

Checks: `python3 scripts/test_resolve_player_names.py`, followed by the existing name/catalog rendering checks. Live search success must be inspected separately from offline tests.
