# Native overlap policies

`adapter.py` exposes the reviewed task-local family in `native_family.py`.
Production v3.1.0 and the canonical reference remain unchanged. The native default
reuses the exact canonical program through the retained `prototype.py`;
`upper_wins` reuses its exact guarded alternate.

## Episode rule and geometry

One private `overlap_precedence` value is fixed for the whole episode:

| Setting | Winner at a true overlap | Input domain | Maximum meaningful input → output |
|---|---|---|---|
| `lower_wins` | Lower panel | Fixed 5 + 1 + 5 rows | 11×30 → 5×30 |
| `upper_wins` | Upper panel | Fixed 5 + 1 + 5 rows | 11×30 → 5×30 |
| `denser_wins` | Panel with more occupied cells; lower on ties | Equal panels, height 5–14; separator height 1 or 2 | 30×30 → 14×30 |
| `sparser_wins` | Panel with fewer occupied cells; lower on ties | Same selector domain | 30×30 → 14×30 |

All settings preserve sole-occupancy cells and aligned blanks. Each panel uses
one nonzero color, distinct from the other panel and the separator. Every panel
row retains a zero, making the separator band unique. Widths are 4–30 in this
separate family; production remains 4–16. Extra rows would be ignored by the
exact canonical program, so its stress claim stops at 11×30.

The selector rules have a global dependency: extract both panels and count their
occupied cells; choose the overlap winner from those counts; apply that winner
at every overlap. A remote occupancy change can reverse an overlap answer while
leaving its two local colors unchanged. The counts are taken before overlay;
counting visible colors after overlay can reverse the comparison.

## Four teaching examples, four queries

The native request contract is **4–6 demos and 1–4 queries independently**.
The first four examples have upper/lower counts `(10,7)`, `(7,10)`, `(5,5)` and
`(20,20)`. The first two have upper color below lower color; the small tie reverses
that palette ordering; the large tie restores it. Each has overlap, upper-only,
lower-only and blank positions. The small tie has opposing row-local imbalances.

Four demos have a concrete cost and purpose. Under the three-demo prefix,
“upper iff upper count > 7” imitates `denser_wins`, and “upper iff lower count > 7”
imitates `sparser_wins`. The large tie rejects both. For either selector, the
upper-winning demonstration is nonextreme in the ordering of either panel's
count, also excluding monotone single-panel thresholds. This does not exclude
arbitrary nonmonotone rules or prove universal identification.

Queries cover a compact 11×4 scene, an ordinary opposite imbalance, a large tie,
and a dense maximum-width scene touching every panel boundary. The selectors'
last query is a substantive 14 + 2 + 14, 30-column input; it is not blank padding.

All six potential demonstrations and the first two queries have matched inputs
across all settings. The last two queries match within the fixed pair or within
the selector pair. This is a documented difference in input domains: larger
geometry reveals the group, but does not distinguish denser from sparser.
Colors, layouts and placements vary with the input seed. The four teaching
regimes and monochrome panels constrain the distribution; no learning gain is
claimed.

Local seed/split/slot streams generate the full six-demo/four-query banks before
slicing. Changing request counts preserves both prefixes. Duplicate retries are
bounded at 64; failure is explicit. Seeds must be literal integers in
`0..2**63-1`, and no global random state is changed.

## Runnable verification

From the packet's outer directory, use its passing Python interpreter:

```bash
WORK/.venv/bin/python review.py run python3 -B -m pytest -q \
  generators/0ae119475d57/tests/test_native_adapter.py \
  generators/0ae119475d57/tests/test_native_audit.py \
  generators/0ae119475d57/tests/test_legacy_public_order.py \
  generators/0ae119475d57/tests/test_parametric_overlap_precedence.py

WORK/.venv/bin/python review.py run python3 -B \
  generators/0ae119475d57/workspace/parametric/audit.py \
  --out ../checks/0ae119475d57/fresh-audit --seed 0 --seed 17

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  0ae119475d57 --seed 0 --seed 17 --demos 4 --queries 4 \
  --out ../checks/0ae119475d57/fresh-qualification --summary
```

Choose new output paths for new executions. The audit executes selected labels
and finite rival programs through protected Racket. Four demonstrations alone
select/refute candidates; a surviving candidate is checked on queries and any
changed answer fails the audit. Rival errors are failures, never refutations.
Selector-specific rivals include post-overlay counts, color sums, row/column
counts, bounding-box area, row-local counts and the opposite tie convention.
Counting exclusive cells in both panels is equivalent to comparing their total
counts and is deliberately not listed as a wrong rule.

`generate` returns private labeled pairs and complete program text. Never send
that dictionary to a learner. `public_turn(episode, index)` returns a fresh,
strictly masked challenge containing only demonstrations and one current query.
It omits answers, settings, seed, program, query count/index, future inputs and
final-turn hints. The first turn is identical for one-query and four-query use.
The existing consumer controls sequencing; this package adds no training loop.

The audit writes canonical visible bytes to hash-derived filenames, sorted by
public ID, and keeps its private binding apart. It rejects duplicate or forged
IDs, malformed grids, leaked fields, mismatched private claims and unindexed
public files. Serialized verification checks the saved bundle; it does not
perform another Racket replay or authenticate a wholly rewritten bundle.

## Legacy evidence and status

`prototype.py` retains its historical two-setting API, multi-query public payload
and count-dependent query slots. Its actual writer now buffers the complete
executed batch and publishes files and private associations in sorted public-ID
order. A protected red/green regression binds that correction; current native
use goes through `adapter.py` and the one-query export above.

Prior prototype receipts remain historical, including the frozen aggregate-test
fixture blocker. Direct focused tests do not claim that an unrelated aggregate
battery passed. The current inventory, qualification and causal replay bind exact
source bytes. Reviewer readiness does not grant owner acceptance or training
admission; the owner must qualify and accept the integrated source natively.
