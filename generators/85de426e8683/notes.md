# Working notes: 85de426e8683

## Current opt-in parametric family

`workspace/parametric/adapter.py` adds `ink_rule=fixed_yellow|target_parity`.
The production generator and selected reference are unchanged; the default
returns the exact canonical program bytes. The alternative counts whole gray
diagonal target components before choosing center ink (odd=2, even=4). The
count is input-dependent and global: a distant extra target changes an existing
target's center without changing its local neighborhood.

The constructive schedule uses 3/4/9 targets in its first three demonstrations.
The four-target example has a 1/3 slope split and three gray near-misses totaling
13 cells. This repairs observed single-slope-count and count-threshold teaching
holes without adding demonstrations. Two-demo episodes restrict query counts
to 3/4; longer lessons query counts 3/5/7/8. All settings share their input draws. Total foreground object counts 6/8/15
in the first three demos reject both all-object parity mappings; two-demo
queries keep total-object parity even to preserve fixed-color identifiability.
Non-gray diagonal triples of color 6/7 explicitly refute color-blind painting.
The canonical sampler's retained color-blind teaching audit remains unresolved:
the new family does not alter or approve that production distribution.

The native adapter supports 2..6 demos and 1..4 queries independently. Larger
scenes are separate prototype support, using 6-cell zones on 12x18 through
30x30 canvases. Distant targets and all-zone distractor content make the largest
case substantive, but the zone lattice/motif palette is a deliberate diversity
limit. Thirty-six declared Python rivals and twelve Racket counterparts bound the
learnability claim; they do not prove universal uniqueness or training benefit.

`workspace/parametric/verify.py` is the reusable label/teaching/export tool. It
retains failures privately, checks matched inputs and first-turn invariance,
and emits public files only after protected-Racket checks pass. Exact commands,
API limits and public/controller projections are in its adjacent README.
The next owner action is exact-source native qualification and acceptance after
integration; reviewer evidence does not confer acceptance or training admission.

## Canonical rule and decisive examples

The selected Racket authority is correct and remains unchanged. It finds
8-connected color-5 objects, selects only objects whose complete normalized
shape is one of the two three-cell diagonals, and recolors the middle cell to
4. Canonical train example 4 and the test example are decisive: each contains a
larger gray object with a tempting three-cell diagonal sub-run that must remain
unchanged.

## Imported generator defects

- **G85-F1 — validator traversal bug.** The imported DFS added every neighboring
  coordinate to the stack before checking color. It therefore walked through
  background and merged remote gray cells conceptually. It then rejected lawful
  larger gray decoys. Reproducer: the canonical inputs; see
  `checks/baseline-selfcheck-console.log` and `checks/tdd-red.log`.
- **G85-F2 — shortcut-compatible distribution.** Ordinary draws contained only
  clean, isolated gray diagonal triples. A learner could fit the local rule
  “recolor the center of any gray diagonal window” and never learn that the
  *whole connected component* must have size three. The canonical near-miss
  family was absent.
- **G85-F3 — dead/ghost axes and stale metadata.** Nine axes were advertised,
  while most were constants, aliases, or bypassed the normal context path. The
  generator also omitted `RULE_HASH`. The baseline linter caught this; see
  `checks/baseline-lint-console.log`.
- **G85-F4 — hard-band manifold drift.** The imported hard band used only
  11..13 by 11..13 grids, outside the canonical 8..10 by 9..11 envelope. The
  intermediate repaired generator retained that range and failed the pinned
  cross-band profile gate; see
  `checks/probe-profile_floor/checks/85de426e8683_after_profile_floor.log` and
  `checks/tdd-red-profile-floor.log`.

## Selected repair

- Same-color-only 8-connected component analysis is now the shared basis for
  validation, axis observation, the Python diagnostic mirror, and competitors.
- The default schedule is a deterministic four-profile curriculum. Every four
  consecutive samples contain both slopes, unrelated colors, multiple-target
  evidence, and at least one larger gray object containing an embedded diagonal
  run.
- A backtracking placer keeps objects one cell apart, preventing accidental
  component merges while allowing semantically hard objects internally.
- Only three exact, observable axes remain: `grid_h`, `grid_w`, and
  `scene_profile`. Unknown overrides and invalid difficulties fail loudly.
- Default dimensions are height 8..10 and width 9..11, preserving difficulty
  banding without abandoning the canonical size manifold.
- Named lesson competitors cover the main shortcuts: local-window semantics,
  either single slope, and first-target-only. `lesson_identifiable` rejects a
  lesson if any declared rival still fits every demonstration.

## Rejected alternatives

- **More clean triples.** Improves surface diversity but leaves the central
  whole-component ambiguity untouched.
- **Random gray noise.** Can create accidental targets or uninterpretable
  components and makes auditability worse. Explicit near-miss motifs give
  controlled semantic pressure.
- **Blank/no-target degenerates in the default curriculum.** They teach
  inactivity but consume a scarce demonstration without distinguishing the
  intended rule from the local-window rival.
- **Keep 11..13 hard grids and add a nominal opt-out.** This would document the
  profile-floor failure rather than repair it; the rule does not require a
  scale shift.
- **Change the Racket authority.** Canonical examples and rule-smoke evidence
  support the existing authority; the defects were in distribution and
  validation.

## Tests and limitations

Task-local tests pin canonical acceptance, canonical rule hash, four-example
lesson coverage, exact override observability, mirror behavior, error handling,
determinism/freshness/global-RNG purity, and the repository's pinned per-band
profile census.

The generator uses representative size-5 near-misses rather than reproducing
all possible larger component topologies (the canonical test includes a
size-6 object). This is deliberate: the lesson teaches the size-equals-three
boundary, while the validator and authority accept arbitrary non-target gray
components. The Python `rule_mirror` is diagnostic only; Racket remains the
label authority.
## Current reviewer considerations

Source SHA-256: `cd7190108b0aea195d4f6516055b93a7e5da642fec382da85bd555c066abc639`.

# Design decisions for `85de426e8683`

## D1 — Preserve the selected Racket authority

**Input choice.** Leave the canonical program and base authority untouched and
pin `RULE_HASH = "810181a298c8"` in the generator.

**Original rationale.** The imported generator did not state why the authority
was omitted from its metadata. Canonical examples, including the larger gray
near-misses, are correctly handled by the existing rule.

**Alternatives considered.** Rewriting the Racket rule; changing connectivity;
or treating every local diagonal run as a target.

**Probe.** Canonical parity, final rule smoke, Racket lint, and authority sync.

**Failure mode avoided.** “Fixing” the data generator by silently changing the
meaning of the task.

**Limitation.** Rule correctness is supported by canonical examples and the
final generated census, not a formal proof over all 30×30 ARC grids.

## D2 — Define targets by complete 8-connected color-5 components

**Input choice.** A target is a whole same-color 8-connected component whose
normalized coordinates equal one of the two three-cell diagonals.

**Original rationale.** The imported validator intended component semantics but
its DFS queued non-gray neighbors, crossed background, and then rejected lawful
larger components (G85-F1).

**Alternatives considered.** Sliding 3×3 windows; four-connectivity; or checking
only component size without shape.

**Probe.** Canonical size-5 and size-6 decoys, generated long/branched decoys,
axis-aligned triples, and `rule_mirror` parity tests.

**Failure mode avoided.** Recoloring a diagonal sub-run embedded in a larger
object, or merging remote gray objects through background.

**Limitation.** Separate diagonal objects touching at a corner become one
8-connected object by design and therefore are not independent targets.

## D3 — Use a deterministic four-profile lesson curriculum

**Input choice.** Cycle `canonical_clean`, `long_diagonal_decoy`,
`branched_decoy`, and `axis_decoys` by `sample_index`; set
`EXAMPLES_NEEDED = 4`.

**Original rationale.** The old random generator emitted only clean isolated
triples. More random clean triples increase visual diversity but do not refute
the local-window rival (G85-F2).

**Alternatives considered.** Pure random motif mixtures; probability-based
near-misses; blank/no-target examples; or a larger curriculum period.

**Probe.** Test all eight cyclic starts, the semantic gate’s 12 materialized
lessons across all bands, and `workspace/probe_curriculum.py`.

**Failure mode avoided.** A complete training lesson accidentally containing no
example that distinguishes whole-component semantics from local-window
semantics.

**Limitation.** A downstream sampler that uses a stride sharing a factor with
the curriculum period could alias profiles. The supplied probe accepts explicit
starts, and the general tooling recommendation in `FEEDBACK_TO_CODEX.md` asks
for stride-aware lesson checks.

## D4 — Include controlled gray near-misses rather than random gray noise

**Input choice.** Use a five-cell straight diagonal, a canonical-style branched
component, and horizontal/vertical triples as explicit decoys.

**Original rationale.** Unknown; the imported generator separated all gray
triples and expressly prohibited larger components.

**Alternatives considered.** Random walks, random speckle, or arbitrary gray
blobs.

**Probe.** Structural classification in `_analyze_scene`, exact profile
observation, and final semantic/profile censuses.

**Failure mode avoided.** Accidental exact targets, accidental component merges,
or visually noisy examples that do not target a named misconception.

**Limitation.** The curriculum is representative, not exhaustive: it does not
generate every size or topology of non-target gray object.

## D5 — Preserve unrelated colors, including pre-existing output color 4

**Input choice.** Every profile includes a separated non-gray distractor; the
axis-decoy profile specifically includes color 4 before transformation.

**Original rationale.** The canonical examples contain unrelated colored cells,
but the imported default generator used only colors 0 and 5.

**Alternatives considered.** No distractors; random multicolor noise; or
forbidding color 4 in inputs.

**Probe.** Four-example coverage test and rule-mirror unchanged-cell assertions.

**Failure mode avoided.** Learning that all non-background cells participate,
or treating every yellow cell as newly produced.

**Limitation.** Ordinary generated distractors are single cells; larger
non-gray objects are not part of this task’s central ambiguity.

## D6 — Keep distinct objects one cell apart with deterministic backtracking

**Input choice.** Translate fixed motifs through shuffled candidate origins and
backtrack until every pair of separate objects has a one-cell Chebyshev gap.

**Original rationale.** The old generator used repeated random placement trials
and an occupied set; no rationale was recorded beyond keeping triples separate.

**Alternatives considered.** Fixed coordinates; unbounded rejection sampling;
or allowing accidental contact and reclassifying afterward.

**Probe.** Determinism/freshness/global-RNG test, 600-draw semantic census, and
120-draw rule smoke.

**Failure mode avoided.** Intermittent generation failures, sample-dependent
component merging, and hidden dependence on global random state.

**Limitation.** Backtracking cost would grow quickly with many more motifs; the
current maximum is small and bounded.

## D7 — Replace nine weak axes with three exact observable axes

**Input choice.** Declare only `grid_h`, `grid_w`, and `scene_profile`; reject
unknown keys and invalid difficulties.

**Original rationale.** The imported axes included singleton fields, an alias,
and degenerate texture branches that bypassed normal behavior. Their intended
independence was not documented (G85-F3).

**Alternatives considered.** Mark every old field diagnostic; retain constants
for compatibility; or expose target count, slope, and decoy count as independent
axes.

**Probe.** `observe_overrides`, explicit profile/size tests, final override gate
(3,960 accepted draws), and final lint.

**Failure mode avoided.** A caller believing an accepted override changed the
returned grid when it did not, or misspelling a key silently.

**Limitation.** Target counts and distractor forms are coupled to named profiles
rather than independently combinable. This is intentional because those
combinations define the teaching curriculum.

## D8 — Match the canonical size envelope in every difficulty band

**Input choice.** Draw heights from `8..10` and widths from `9..11`, retaining
`draw_int_diff` difficulty bias inside that envelope.

**Original rationale.** The imported hard branch used 11..13 dimensions,
possibly to make “hard” mean larger. No task-semantic reason was documented.

**Alternatives considered.** Keep 11..13 and declare a profile opt-out; add one
rare canonical-size hard anchor; or eliminate difficulty variation entirely.

**Probe.** The repository’s exact pinned 20-draw-per-band census, reproduced in
a task-local test. The intermediate range failed hard-band support 0/20 before
the repair (G85-F4).

**Failure mode avoided.** Training the hard band only on off-manifold scale and
allowing pooled easy/medium support to conceal it.

**Limitation.** Difficulty now changes size only within a narrow range; semantic
difficulty comes mainly from scene profiles and near-misses.

## D9 — Add executable lesson competitors and a reusable probe

**Input choice.** Declare four rivals: local diagonal windows, main-slope-only,
anti-slope-only, and first-target-only. Add `lesson_identifiable` and
`workspace/probe_curriculum.py`.

**Original rationale.** No lesson-level identifiability contract existed.

**Alternatives considered.** Hand-written prose only; aggregate witness
frequencies; or model inference as the gate.

**Probe.** The tool dynamically iterates the generator’s actual competitor map,
checks complete overlapping lesson windows, records source hash and denominators,
and exits nonzero on any survivor.

**Failure mode avoided.** Declaring a witness somewhere in the corpus while a
particular assembled lesson still permits the shortcut.

**Limitation.** The probe is tied to declared rivals; an undeclared misconception
can still survive. It uses the tested Python mirror for speed, while the full
battery separately verifies Racket parity.
