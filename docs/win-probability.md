# Game outcome estimates

Game cards show probabilities only when a current published full-match model matches the exact league, event, teams and kickoff. Unmatched games show no percentage. The former recent-results estimate is retained only for internal tests; it was not calibrated as a real-world probability.

Team strength combines available season win-equivalent rate (50%), recent five games (35%) and home/away record (15%). A draw counts as half a win. Each input adds four neutral wins over eight neutral matches to reduce small-sample extremes. Available component weights are renormalized. Missing team data is neutral, never inferred from the team name.

The difference in log odds is multiplied by 0.65 before converting to the head-to-head estimate. This reduces extreme estimates from short streaks. Soccer has an explicitly assumed 26% draw prior; KBO/NPB/CPBL have a 3% draw prior. The draw prior has ten pseudo-matches and is updated using both teams' available recent draw results. Other sports use two outcomes, including overtime/shootouts for hockey.

With no team records, the card labels its numbers as a neutral baseline: soccer 37/26/37, two-outcome sports 50/50. These numbers are assumptions, not evaluated team-specific predictions. Partial records are labeled explicitly. Percentages are rounded to tenths using largest remainders, preserving a 100% total.

The model runs again whenever the current game data is refreshed. It uses completed games before both the event kickoff and current time. Soccer summary record order is deliberately ignored because provider summary formats differ. NHL third-column overtime losses count as losses.

Validation: `node scripts/check-win-probability.mjs`.

## Published probabilities take priority

`update-external-forecasts.py` collects original published full-match probabilities from ESPN Matchup Predictor, Sports Mole match analysis and BK Volley match forecasts. Google locates these publishers; Google search summaries and AI overviews are not probability sources. Picks, exact-score chances and set-win probabilities are excluded. Sports Mole sentence order can vary, so the parser identifies each team's full-match win and the draw separately.

The feed retains publisher, original URL, raw probabilities, event ID, both team IDs, kickoff and retrieval time. Sports Mole matching requires exact league and normalized full team identities; a maximum 90-minute source timestamp tolerance accommodates its observed JSON-LD DST inconsistency. The output always uses the schedule's actual event identity and kickoff. KOVO uses stable match IDs plus both teams and the Korean calendar date. Its publisher explicitly marks its model uncalibrated.

The browser requires event, league, both side IDs and kickoff to match. Entries expire two hours after retrieval. Unavailable or expired entries are hidden. The branded heading remains `NUDE TV AI 승부예측`. Sources stay in review metadata; external links are not added to game cards. Rounded values sum to 100.0%; source raw totals must be within 0.5 percentage points of 100.

GitHub Actions refreshes the feed on a 15-minute schedule (GitHub may delay runs). The page fetches the current feed at refresh and during its existing five-minute refresh cycle. A failed fetch never extends an old probability's freshness. This is not a guarantee of predictive accuracy or complete coverage across all leagues.
