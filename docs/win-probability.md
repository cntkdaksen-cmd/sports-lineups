# Game outcome estimates

Every game card shows statistical estimates. These estimates have not been backtested or calibrated as real-world probabilities. They do not include live score, lineup, injury, bookmaker or external prediction data.

Team strength combines available season win-equivalent rate (50%), recent five games (35%) and home/away record (15%). A draw counts as half a win. Each input adds four neutral wins over eight neutral matches to reduce small-sample extremes. Available component weights are renormalized. Missing team data is neutral, never inferred from the team name.

The difference in log odds is multiplied by 0.65 before converting to the head-to-head estimate. This reduces extreme estimates from short streaks. Soccer has an explicitly assumed 26% draw prior; KBO/NPB/CPBL have a 3% draw prior. The draw prior has ten pseudo-matches and is updated using both teams' available recent draw results. Other sports use two outcomes, including overtime/shootouts for hockey.

With no team records, the card labels its numbers as a neutral baseline: soccer 37/26/37, two-outcome sports 50/50. These numbers are assumptions, not evaluated team-specific predictions. Partial records are labeled explicitly. Percentages are rounded to tenths using largest remainders, preserving a 100% total.

The model runs again whenever the current game data is refreshed. It uses completed games before both the event kickoff and current time. Soccer summary record order is deliberately ignored because provider summary formats differ. NHL third-column overtime losses count as losses.

Validation: `node scripts/check-win-probability.mjs`.
