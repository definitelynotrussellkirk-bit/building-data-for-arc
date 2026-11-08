# Tooling feedback

F1: Add an explicit setting selector to `review_witness template`

Symptom: the helper always chose the first nondefault qualified episode, but the useful causal branch for `96d4a788da47` was the later `nearest` setting. Evidence: the initial recipe selected episode 2 (`right`) and had to be edited to episode 4 (`nearest`). Suggested change: accept `--settings-json` or `--episode-index`, validate it against the qualified execution, and retain the current first-nondefault behavior as the default.

F2: Report the inspected bundle count in `check_first_turn.py`

Symptom: the combined report contained the `bundles` array and all aggregate counters but no direct `bundles_checked` scalar, making compact summaries infer the count. Evidence: this run inspected two bundles and returned 48 public views/12 first turns, while `bundles_checked` was absent. Suggested change: emit `bundles_checked = len(report["bundles"])` beside the other totals.
