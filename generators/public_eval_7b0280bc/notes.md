# public_eval_7b0280bc — graph route selection

## Design and implementation plan
Infer the background, square node colors, and irregular eight-connected path
segments. The color shared by exactly two squares identifies the endpoints.
Build a graph by attaching each path component to its two touching nodes.
Canonical `route_metric=fewest_edges` selects the minimum-hop endpoint route;
paint its segments gray (5) and intermediate squares green (3), retaining the
endpoint squares. A lexicographic reading-order node sequence breaks ties.

The alternative `least_ink` minimizes the sum of path-component pixel counts,
not hop count. A long two-edge detour competes with a shorter multi-edge route;
side branches, diagonal joins, thick paths, palette and D4 transforms vary.
A produces the input-dependent graph and selected node/edge sequence; B paints
exactly those components. Substituting the hop route for the least-ink route is
a protected causal counterexample.

- [x] Verify all supplied original labels through a new general Racket rule.
- [x] Implement self-contained sampler and identical local native resource.
- [x] Test count/types, full query bank, route ties, diagonal paths and relocation.
- [x] Attack geometric/connectivity/edge-metric rivals and repair lesson findings.
- [x] Freeze source; preflight, causal replay, and single-query export verification.

No owner catalog or approval edits. Author self-review is not independent review.

## Verified final build
All five planned steps completed. The final staged task suite has 64 passing
checks; the independent protected-Racket audit covers 12 episodes, 92 label
claims, 40 distinct executions and 156 named-rival checks. All four supplied
original labels (including test gold) match. Authoring preflight is passed for
both settings at seeds 17 and 43, two demonstrations and four queries.
The 30x30 wrong-route causal witness changes 187 cells; fresh protected replay
passes. Sixteen single-query public views pass the official export checker.

The first audit exposed first/last reading-order path shortcuts. The second
teaching profile now has four possible routes and a correct route strictly
between the reading-order extremes. Both metrics agree there, refuting a
longest-ink rule. Other profiles separate the metrics, vary route node counts,
and retain diagonal joins and unselected branches. Bounded geometry tests and
independent Racket replay cover the changed construction. Initial failures and
RED-to-GREEN regressions are retained, not presented as passing runs.

## Supported grammar and limits
Four structurally identifiable colors, modal background, same-color square
nodes of side at least two, exactly two endpoint-colored squares, and each
8-connected pipe component adjacent to precisely two nodes. Generated paths
use 2x2 or 3x3 nodes and one- or two-pixel segments. Canonical shortest-hop ties
use the complete node reading-order sequence; ink ties use the same convention.
The generator constructs a finite graph family, not every graph embedding.
Agreement profiles deliberately choose a view that defeats reading-order rules.
The separate graph-only boundary census predates that last teaching change;
the final combined census and staged tests bind the final generator hash.

## Reuse
From the packet outer directory, run through `review.py run`:
- `python3 generators/public_eval_7b0280bc/workspace/parametric/audit.py audit --out ../checks/NEW-AUDIT`
- `python3 -m arcpuzzles.review_public_creation preflight public_eval_7b0280bc --root . --out ../checks/NEW-PREFLIGHT`
- `python3 generators/public_eval_7b0280bc/workspace/parametric/audit.py finalize --preflight ../checks/NEW-PREFLIGHT/preflight.json --out ../checks/NEW-FINAL`

Choose fresh output directories. Source changes require a new preflight and
causal/export binding. `checks/runtime_smoke.py` runs registration, generation
and staged tests only inside a disposable copy; it never approves a family.
Self-review by the author is not an independent review. Owner registration,
source approval, fresh native qualification and acceptance remain pending.
