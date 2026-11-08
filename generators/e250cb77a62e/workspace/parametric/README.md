# Native stamp-created connectivity

Parameter: `stamp_policy = all_stamps | largest_joined`.
The default loads the selected canonical Racket bytes exactly. The alternative
executes that same stencil stamping, computes four-connected cyan regions in the
result, and recolors the unique largest region green (3). It leaves all other
stamped cells cyan (8), and preserves the blue/yellow source frame.

## Design and admitted grammar
A extracts the yellow stencil from the blue frame and stamps it at every orange
anchor. The intermediate is the union of newly stamped cells and its exact
four-connected regions. B selects the largest region by occupied-cell count and
recolors only that region. Original anchors and frame bounding boxes do not
determine the grouping: staircase footprints can touch orthogonally, meet only
diagonally, or overlap at exactly one cell. A smaller occupied region can have a
larger bounding box. This makes the dependency geometric rather than a cosmetic
color substitution.

`native.py` constructs connected staircase stencils with variable internal
branches, both transposed orientations, two/three/four-copy joined groups,
aligned-but-disconnected distractors, one-cell-overlapping pairs, and isolated
stamps. Inputs are setting-neutral. The opt-in grammar extends the unchanged
production sampler (11..22, 1..4 disjoint stamps) to 18..30 canvases, more anchors
and controlled contact/overlap. All complete footprints remain in bounds and
outside the source frame. The existing exact Racket authority supports this
extension without any rule change. It is not claimed to pass the old production
sampler's stricter distribution validator.

The fourth query is 30x30, with a 5x5 stencil, a 7x7 source frame, fourteen anchors,
a four-copy winning component, five aligned distractor copies, a shared-cell pair
and three isolated copies. It touches every input boundary and all quadrants.
The cyan/green output contains at least 125 stamped cells before variable stencil
branches add more. This is populated stress content, not padding.

## Native API and privacy
`adapter.program(settings)` returns the exact setting program.
`adapter.generate(seed, settings, demos, queries)` accepts exact integer counts
2..6 and 1..4 independently. A full controller lesson stores four novel queries;
smaller counts are stable prefixes, even when demo counts change.
`native.public_turn(episode, query_index)` returns a detached, strictly masked
single-query view. Private programs, settings, seeds, answers, future queries and
total-count hints never belong in the public turn or its content hash.

## Teaching repair and finite rivals
An executable shortcut initially fit BOTH minimum-count demonstrations: recolor
any component of exactly twice the prototype area. It disagreed on larger query
groups. The second demo now uses THREE copies; the minimum remains two demos.
The before/after protected-Racket replay is in
`checks/e250cb77a62e/two-copy-before.json` and `two-copy-after.json`; six evaluations
per version establish the failure and repair on the same retained seed/query.

The executable bank compares both settings plus all-green, smallest, first,
last, eight-connected, bounding-box-joined, component-bounding-box-area, and
exactly-two-copies rules. Both demos also distinguish actual overlap area from
bounding-box area and four-connectivity from diagonal contact. A finite rival
bank is not a proof against every possible rule or threshold overfitting.

## Reusable audit and replay
`audit.py` is a self-contained copy of the already tested generic task-local
native auditor; it imports only adjacent `native.py`, not another task or checkout.
It checks all count combinations, matched inputs, distinct grids, prefix stability,
masking/private-field invariance, source hashes, finite teaching, protected-Racket
parity of every rule, and public hash-named files with exactly one query each.
It saves labeled four-query episodes and hypothesis programs separately in private/.

```sh
python3 review.py run python3 generators/e250cb77a62e/workspace/parametric/audit.py --seeds 20 --out ../checks/e250cb77a62e/audit-new
python3 review.py task-tests e250cb77a62e --phase after --out ../checks/e250cb77a62e/tests-new
```

The legacy test suite's hard-coded canonical-data depth was repaired using
`reviewer_support.find_root` and `canonical_pairs`; its semantic assertions remain.
The first combined long audit command was interrupted by the outer tool deadline;
its incomplete directory is not evidence of success. The final bounded run uses
`checks/e250cb77a62e/audit-final/` and a recorded command exit status.

Source/evidence inventory, native qualification, execution receipt and protected
wrong-intermediate witness are separate gates. Reviewer readiness is NOT owner
exact-source acceptance or training admission. Final review is author self-review;
finite tests do not establish universal induction, sampler success or training gain.
