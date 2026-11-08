# c1fd38e5812b Repair Kit Changes

## Built changes

- Replaced the assigned generator with version `3.1.0` while preserving the
  canonical five public profiles and their 25% mixture weight.
- Added independent `uniform_rows` and `uniform_cols` extrapolation profiles.
- Re-pinned `RULE_HASH` to the normalized selected canonical rule hash
  `0805714fcf25`.
- Made task tests portable through `reviewer_support.find_root` and
  `reviewer_support.canonical_pairs` rather than a fixed parent-depth path.
- Added a literal independent-axis counterexample and tests that distinguish
  the repaired generator from a row/column-coupled rival.
- Added an executable six-member parametric Racket rule family with hidden
  settings, greedy lesson selection, four distinct query grids, private
  answers, content-addressed public files, and leakage tests.
- Recreated the contamination-safe blind solution and accompanying notes from
  the pre-reference solve recorded before the interrupted workspace reset.
- Added `apply_repair.py`, a fail-closed source-hash-guarded applicator with
  backups, receipts, optional official checks, optional packaging, and
  preservation of user-edited audits/reports on later runs.
- Added `verify_kit.py`, a self-contained local preflight for future agents.

## Deliberately not claimed

The repair kit does not claim that the restored full packet has passed the
fresh 2,500-seed battery, four-query official generator run, clean-context
manual audit, post-repair blind re-solve, or official package validation. Those
require the original 350 MB packet, which the upload service did not
rematerialize after the execution workspace reset. `apply_repair.py --verify`
runs the available official commands once the kit is applied to that packet.
