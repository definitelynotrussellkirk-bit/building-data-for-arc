# b6c499e1fa78

0-background square grid, now supported from 10×10 through 30×30. A three-row blue wall in the top half contains one to three connected opening pockets. Below it, separated by a blank row, are gray key components. The exact canonical rule turns a gray key red when either:

1. some cell has at least three gray four-neighbors, or
2. the key's top rows, at the opening's height, match an opening directly or left-right mirrored.

Ordinary draws contain exact, observable counts of matching keys, one branch-only key, and nonmatching/nonbranching negatives. Controls reject unknown or coercive values and support substantive 30×30 scenes.

## Native parametric family

- `branch_policy=unconditional`: byte-exact canonical match-or-branch behavior.
- `branch_policy=matched_area`: first derive the set of **full occupied areas** of opening-matching keys, then recolor a branched key only when its full area is in that input-derived set. Matching keys still recolor directly.

The family uses matched setting-neutral inputs, 2–6 demonstrations, four distinct controller-side queries, crossed fixed-dimension intermediate controls, and a 30×30 boundary/density stress query.

Kind: `per_puzzle`. Reviewed generator version: `4.0.0`. Owner source review and native acceptance remain separate.
