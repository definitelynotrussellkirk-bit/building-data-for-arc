# Working notes: e78f94d8f5bc

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `92d7322e92d454be7e44ee31cdf557008e8faa7e55e3d70a7173dedf4e165bae`.

# Decisions for `e78f94d8f5bc`

## D1: Break the fixed lattice with shape-preserving orientations

**Selected.** Generate the same lawful perfect maze, then independently choose identity, horizontal reflection, vertical reflection, or 180° rotation. This preserves the exact requested `(grid_h, grid_w)`, path length, turn count, uniqueness, off-path branches, and palette while moving the coarse-maze lattice among all four modulo-2 phases.

**Why.** The baseline probe found endpoint parity and wall-lattice collapse in all 1,800 fixed-axis samples. The same probe on the selected source found all four parity phases, while task tests and the authority battery remained green. Evidence: `checks/shortcut-probe-before.json`, `checks/shortcut-probe-after.json`, and `checks/task-tests/result.json`.

**Rejected alternatives.** A 90°/270° rotation or transpose would exchange height and width and violate exact rectangular overrides. Padding or translation would change dimensions or maze topology. Rebuilding the maze on a randomized phase before carving was more invasive and duplicated logic already guaranteed by a post-generation isometry.

## D2: Make every four-pair window query-rotation safe without adding demonstrations

**Selected.** Use the period-four size schedule `(10×10, 10×10, 5×5, 6×6)` and turn schedule `(4, 4, 2, 3)`, with different band offsets. A lesson still has three demonstrations and one query, but the four underlying pairs contain duplicate witnesses for both categories whose absence lets the declared conditional rivals survive.

**Why.** The orientation-only source had 0/300 ordered ambiguities but 334/1,200 ambiguous query rotations. The selected schedule reduced both production and rotation ambiguity to zero in 300 lessons / 1,200 rotations while preserving all three canonical sizes and turn counts. Evidence: `checks/lesson-census-before-schedule.json`, `checks/rotation-tdd-red/`, `checks/rotation-tdd-green/`, and `checks/lesson-census.json`.

**Rejected alternatives.** Increasing to five or six demonstrations would spend more lesson budget than needed. Removing `skip_10x10` or `skip_four_turn_routes` from the rival declaration would hide rather than repair the teaching defect. Keeping an ordered-only curriculum would contradict the package's required arbitrary-query-rotation check.

## D3: Keep tests portable and behavior-focused

**Selected.** Resolve the repository/canonical location through `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`, and search deterministic generated cases for the one-wall ambiguity fixture instead of assuming one historical seed always has it.

**Why.** The original fixed `parents[...]` lookup failed in isolated replay layouts, and orientation changed which exact seed supplied the ambiguity without changing the required behavior. The selected tests still assert the semantic property and now run from the packet runtime. Evidence: the progression `checks/tdd-red/` → `checks/tdd-green/` → `checks/tdd-green-2/`, followed by `checks/task-tests/result.json`.

## D4: Do not change the Racket authority or canonical examples

**Selected.** The defect was in generated distribution and lesson assembly, not in the shortest-path rule. Rule hash `6726820f442b` and canonical data remain unchanged; final Racket application agrees with the Python mirror on the retained shortcut witness (`checks/question-witness-comparison.json`).

**Rejected alternative.** Editing canonical examples merely to refute the boundary rival would alter the reference task and was outside the necessary repair. The generator now emits abundant lawful counterexamples instead.

## D5: Preserve and extend prior design constraints

Associated notes from assignment copy `local-random-a8cd7df7587f` were treated as constraints rather than overwritten. In particular, `GNOTE-003658` supports perfect mazes for unique paths, `GNOTE-003660` motivates at least three demonstrations, and `GNOTE-003662` forbids arbitrary palette permutation. The selected changes preserve all three decisions.

## D6: Retain honest limits

The 300-lesson census is strong sampled evidence against the declared rivals, not a proof against every possible shortcut. The final generator intentionally retains perfect-maze topology and canonical size/turn families; broadening topology would require explicit shortest-path counting and a separate design review rather than being bundled into this repair.

## D7: Add a native episode-fixed branch policy without changing the canonical default

**Selected.** The adapter exposes `branch_policy` with `path_only` and `largest_branch`. `path_only` returns the canonical Racket source byte-for-byte. `largest_branch` preserves endpoint discovery and obstacle-aware shortest-path painting, then marks the largest zero-region left after the path becomes a barrier.

**Why.** The alternate setting composes directly with the task's existing maze reasoning instead of replacing it with a cosmetic palette or geometry switch. Inputs are sampled independently of the hidden setting, so matched seeds have identical demonstrations and queries under both policies. Evidence: `workspace/parametric/promotion.json`, `workspace/parametric/canonical.rkt`, `workspace/parametric/largest_branch.rkt`, and `checks/e78f94d8f5bc/qualification/`.

## D8: Treat the painted path as the required causal intermediate

**Selected.** Step A computes and paints the unique obstacle-aware endpoint path. The intermediate is that path plus the row-major off-path regions induced by removing it from the walkable tree. Step B selects the largest induced region, recolors it 8, and restores the endpoints.

**Why.** Before A, the walkable zeros are one connected tree; the branch candidates used by B do not yet exist. The retained protected-Racket witness uses a qualified 6x10 query with branch sizes `[10, 2, 2, 2]`. Replacing A with a skip-path program changes the final label. Evidence: `checks/e78f94d8f5bc/causal/witness.json` and `checks/e78f94d8f5bc/causal/replay.json`.

## D9: Build teaching and stress data around matched visible inputs

**Selected.** Support every demonstration count from 2 through 6 and exactly four distinct queries, exposed one at a time. The first three queries vary rectangular geometry and route complexity; the fourth is a 30x30 expanded spanning-tree maze with 449 non-wall cells and occupancy in all four quadrants. Deterministic scene caches make repeated cross-setting and cross-demo-count audits reuse identical draws.

**Why.** This keeps rule inference, rather than input distribution, as the setting distinction and makes the public first turn equivalent to single-query evaluation. The cache is only a performance optimization over deterministic generation; it does not change sampled bytes. Evidence: `workspace/parametric/prototype.py`, `workspace/parametric/audit.py`, and `checks/e78f94d8f5bc/audit-stdout.json`.

## D10: Retain a finite executable rival audit and honest admission boundary

The audit executes the declared rule and six plausible rivals: alternate setting, all branches, smallest branch, first branch, last branch, and largest original zero-region without first painting the path. Both 3-demo public lessons reject all six, all four queries replay through protected Racket, and a 50-seed sweep covers both settings and demonstration counts 2..6. This is bounded evidence against authored shortcuts, not a proof of universal identifiability or training gain. Owner exact-source acceptance remains pending and `training_admitted` remains false.

