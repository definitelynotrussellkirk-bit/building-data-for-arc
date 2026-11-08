# Blue-contact graph: whole cluster or two hops

`selection=whole_cluster` returns the exact selected canonical Racket source.
`selection=two_hops` extracts the same monochrome cardinal components, traverses
two object-contact edges from the unique blue object, then constructs the
row-major adjacency matrix induced by that input-dependent reachable set.
Colors remain 1 on the diagonal, 8 on an edge, 0 otherwise.

A = extract the object-contact graph and expand reachability twice.
Intermediate = object IDs within shortest graph distance at most two from blue.
B = size/order/render the adjacency matrix only on those IDs.
The counterfactual omits the second expansion; the retained path query changes
from a 3x3 matrix to 2x2. This is derived-set selection, not iterative physical
simulation. The full-cluster default is not redefined.

## Native interface

`program(settings)` and `generate(seed, settings, demos=3, queries=4)`.
Exact nonnegative integer seeds; 2–6 demonstrations, 1–4 prefix-stable queries.
Full episodes always request four queries. Unknown keys/counts/types fail closed.
Inputs are matched across settings and query draws do not depend on demo count.
Python outputs are claims; the native qualifier re-executes them in protected
Racket. Do not use unchecked Python claims as production training labels.

The first two examples teach a bent path and a cyclic branching graph. The first
has 28 selected cells and a connected 50-cell non-blue distractor, constructively
refuting the larger-area shortcut. Extra lessons vary topology and root position.
Four queries cover 8x13, 17x23, 24x21 and 30x30. The latter stretches actual objects
and distractors across all four borders, with at least 200 occupied cells.
The separate prototype extends size support beyond the production 18x20 envelope;
the canonical graph rule itself is dimension-independent. Production is unchanged.

Finite self-review covers whole/two/one/three-hop and exact-distance selection,
all objects, largest area, path-by-count, color/BFS ordering, diagonal contact,
spatial distance and global color nodes. It is not a proof against arbitrary rules.
The motif family is deliberately bounded: six topologies with D4 orientations,
root/color/layout/scale/corner variation, not unrestricted planar graphs.

## Reproduce (from the outer packet)

```sh
python3 review.py run python3 generators/8069b5294ce4/workspace/parametric/verify.py --out ../checks/8069b5294ce4/audit-fresh
python3 review.py task-tests 8069b5294ce4 --phase after --out ../checks/8069b5294ce4/tests-fresh
python3 review.py run python3 -m arcpuzzles parametric qualify 8069b5294ce4 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/8069b5294ce4/qualification-fresh --summary
```

The verifier stores protected-Racket four-query examples, a bounded Python claim
sweep, causal cases, and hash-named public single-query views. `public_turn` copies
only demonstrations and the current input: no setting, program, answer, future
input, turn number or total-count hint. `negative/` deliberately exposes an answer
and must fail the packet's public checker; never send that directory to a model.
The current evidence manifest binds sources and scoped checks, not acceptance.
Owner qualification/acceptance and downstream training admission remain separate.
