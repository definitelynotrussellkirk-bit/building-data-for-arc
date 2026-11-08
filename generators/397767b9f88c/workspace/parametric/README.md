# D4 equality matrix with largest equivalence blocks

The exact canonical default is `finish=all_matches`: extract color-blind
4-connected objects in top-left order and write `2` wherever two object masks
match under any of the eight dihedral transforms.

The composed setting is `finish=largest_equivalence_blocks`. Step A builds the
same complete equality matrix. Step B finds four-connected red components in
that matrix, retains every component tied for greatest area, recolors retained
cells to `8`, and sets all other cells to zero. Thus Step B consumes the
relation matrix rather than the original object grid. The retained protected
counterfactual selects largest *input objects* before relation construction;
it changes the answer when a small shape has the largest equivalence class but
a larger singleton distractor exists.

Three demonstrations are sufficient. They construct class multiplicities
3/2/1, 2/2/1, and 4/1/1, teaching a unique winner, global ties, and that class
population—not object area—controls the second stage. Every scene includes a
positive pair that requires a diagonal reflection, repairing the prior lesson
hole where rotations plus horizontal/vertical reflections survived. A same-area
same-bbox negative pair also rejects size and box shortcuts.

`generate(seed, settings, demos=3, queries=4)` supports stable prefixes with
3–6 demonstrations and 1–4 independently selected queries. Both settings share
identical inputs. The ten-scene bank includes four distinct novel queries and a
30x30 case with ten disconnected area-eight objects (80 nonzero cells), content
in every quadrant, and all four boundary contacts. Seeds and numeric controls
reject booleans and out-of-range values.

The finite rival bank covers diagonal-only, all-equivalent, area, bbox,
rotation-only, six-transform axis-reflection-only, exact-orientation,
recolor-all, first-block, first-largest-only, and wrong-order input-area rules.
This is bounded evidence, not universal uniqueness. Owner acceptance and
training admission remain separate.
