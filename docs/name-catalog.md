# Reviewed names and full club names

`dist/name-catalog.json` is the public name feed consumed on every site refresh. The browser falls back to its bundled catalog when GitHub is unavailable.

Approve full team names and provider aliases in `scripts/team-name-review.json` and `dist/team-ko.json`. Add established player names to `dist/player-ko.js` or `scripts/player-name-review.json` (`userOverrides`). Keep club/player identity and source evidence in the review files. Do not infer identity from surnames or publish unverified search snippets.

The name workflow independently builds and validates the approved catalog every 15 minutes and whenever review sources change. The existing lineup workflow collects new names across every league. It uploads unreviewed names with Google and Naver search links in `name-review-queue.json`. Search evidence still needs review before approval. Approved catalog updates reach the site without a new frontend deployment.

Run locally:

```sh
node scripts/build-name-catalog.mjs
node scripts/check-player-names.mjs --inventory scripts/fixtures/player-name-inventory.json --require-reviewed
```
