# Working notes — 28aab6c2d6e0

## 2026-10-03 — assignment review-c16985b4128987c4

The immutable selected baseline was generator `2.1.0`, SHA-256
`b3dbd88a9c0d01bb03e3cf8e3e4af93d72ec0ab650a9ac789a3a49c0d19f684c`.
Its source, summary, and validator encoded a narrower and incorrect rule: complete only
three-cell L-trominoes to solid 2×2 squares and leave non-L objects unchanged. The canonical
Racket authority instead fills every nonzero connected object's tight bounding rectangle.
Associated prior notes were empty; no prior return patch was used as a lead.

The completed baseline battery reported 7 green, 2 advisory, and 3 failed stages. Lint and
defect lint identified dead/contradictory contract surface. Override checking recorded 4,050
mismatches, 1,110 generation errors, and acceptance of unknown keys. The selected Racket
authority itself was synchronized and was not changed.

Version `3.0.0` replaces the generator contract rather than extending the L-only grammar.
It produces 2–4 separated, rule-active irregular components on 7–8 by 7–9 grids, uses exactly
two sampled nonzero colors, guarantees at least one non-L component, and schedules a
repeated-color scene in every three examples. The only exact public controls are grid height,
grid width, and object count. Unknown or invalid controls fail loudly.

Executable semantic support includes a pure Python authority mirror, strict task predicate,
override observer, canonical shortcut declaration, three rivals, three witnesses, and a
lesson-identifiability check. `workspace/semantic_probe.py` stress-tests actual declared
rivals and witnesses. Its retained 100-lessons-per-band run checked 300 lessons / 1,200
examples: 0 strict failures, 0 surviving rival windows, and 1,199 unique inputs.

Tests were written and run before replacing production source: the baseline failed 9 and
passed 2. Final portable task tests pass 11/11, including all canonical pairs and 30 generated
Racket-parity examples. The full final battery is 12/12 green. Final generator SHA-256:
`ea24b149fc1cbf74819a3861454acad5ef8149170fef792bf69db03f0e546a2c`.

Known limits: fixed canonical-scale dimensions; finite shapes fitting 3×3 slots; exactly two
colors; disjoint component bounding boxes; no identity/full-rectangle examples; no overlapping
or overwrite-order cases; and no claim that the declared rival set is exhaustive or that a
particular learner will infer the rule.
## Current reviewer considerations

Source SHA-256: `ea24b149fc1cbf74819a3861454acad5ef8149170fef792bf69db03f0e546a2c`.

# Decisions — 28aab6c2d6e0

## Source of truth and repair boundary

The canonical ledger says: on a fresh zero canvas, independently fill the tight bounding
rectangle of every nonzero 4-connected monochrome component with that component's color.
The imported generator instead implemented only “complete 3-cell L-trominoes to 2×2.”
Because the selected Racket program already matched all canonical outputs and authority-sync
was green, the repair changed the Python generator and its task-local support files only.
No Racket or canonical-data edit was justified.

The associated-notes file contained no prior findings, and no earlier return patch was used.
The frozen baseline battery and direct canonical inspection supplied the initial evidence.

## D1 — Replace the legacy object grammar rather than patch it

**Choice.** Generate 2–4 separated irregular monochrome components and let the existing
canonical Racket rule fill every component's bounding box.

**Why.** The legacy grammar encoded the wrong task boundary: “is this object an L?” rather
than “what are all connected objects?” A local addition of one or two non-L shapes would have
left the validator, metadata, and lesson semantics coupled to the false rule.

**Rejected alternative.** Keep the L-tromino generator and broaden a texture branch. This
would retain a high probability of L-only lessons and would not repair the source summary or
semantic contract.

**Probe.** Canonical inputs are accepted and the Python mirror equals all three authoritative
outputs. Racket parity covers those three pairs plus 30 generated cases in the final task test.

## D2 — Stay on canonical-scale dimensions

**Choice.** Expose exact `grid_h` in 7..8 and `grid_w` in 7..9, with a deterministic
three-lane schedule `(7×7, 7×8, 8×9)`.

**Why.** The public examples live at this scale. Broad 6..13 by 7..15 dimensions in the
baseline added size variation while its actual semantics were wrong. Canonical-scale scenes
make the intended object decomposition visible without padding dominating the lesson.

**Rejected alternative.** Preserve broad dimensions for nominal diversity. This was lower
value than semantic diversity and made exact overrides difficult to honor consistently.

**Measured result.** In each 400-example band sample, dimensions occurred 134/133/133.

## D3 — Use 2–4 objects with exactly two nonzero colors

**Choice.** Easy defaults schedule 2/3/2 objects, medium 2/3/4, hard 3/4/4; exact overrides
can request any 2..4. Every input uses exactly two sampled nonzero colors, assigned
alternately in reading-order placement.

**Why.** Two objects establish the universal quantifier. Three or four objects force at least
one color to appear in disconnected components, making object identity distinct from color
identity. Exactly two colors also keeps the relation legible on small grids.

**Rejected alternatives.** Distinct colors for every object makes “one box per color”
indistinguishable from the intended component rule. A single repeated color everywhere
would remove useful evidence that color is preserved per object.

**Failure mode controlled.** The repeated-color components have separated bounding boxes;
the global per-color box strictly includes background between them, producing an observable
rival disagreement.

## D4 — Require every object to expand and every scene to contain a non-L object

**Choice.** Components come from a bounded library of connected shapes whose tight rectangle
contains at least one missing cell. Each scene includes at least one shape that is not a
3-cell L in a 2×2 box.

**Why.** A full rectangle is an identity branch and supplies no evidence for filling. An
all-L scene permits the baseline's wrong special-case rule. Requiring a non-L expansion in
every example makes the general bbox operation locally visible.

**Rejected alternative.** Rely on aggregate frequency across a batch. Individual lessons
could still consist entirely of Ls, so the shortcut could survive where it matters.

**Measured result.** `l_tromino_only` disagreed on all 1,200 stress examples.

## D5 — Keep components and bounding boxes disjoint

**Choice.** Components are separated, and their tight bounding rectangles do not overlap.

**Why.** The selected authority paints objects in an iteration order. If rectangles overlap,
output colors can depend on ordering rather than solely on the intended local operation.
Disjoint rectangles make every component's contribution independently checkable.

**Rejected alternative.** Add overlapping rectangles as hard examples. The canonical pairs
do not establish collision semantics, so this would teach an incidental implementation detail.

**Limitation.** The generator does not cover overlapping, nested, or overwrite-order cases.

## D6 — Advertise only exact, observable controls

**Choice.** The public axes are `grid_h`, `grid_w`, and `n_objects`. Unknown keys, invalid
difficulties, wrong types, and out-of-domain values fail loudly. Every returned grid exposes
all three values through `observe_overrides`.

**Why.** The baseline advertised numerous textures and controls that generation ignored,
clamped, or contradicted. A smaller honest contract is more useful than a broad dead one.

**Rejected alternative.** Preserve aliases for compatibility. There was no evidence that
those aliases represented meaningful task dimensions, and silent acceptance caused the
baseline override failure.

**Measured result.** Final override gate passed 2,880/2,880 accepted draws over 32 cases and
three bands with no mismatch or rejection.

## D7 — Make lesson identifiability executable

**Choice.** Declare three rivals: `per_color_bbox`, `l_tromino_only`, and
`first_object_only`; declare witnesses connecting generated facts to those rivals; implement
`lesson_identifiable`; set `EXAMPLES_NEEDED=3`.

**Why.** A statement such as “repeated colors are sometimes present” does not prove each
teaching unit eliminates the shortcut. The three-lane schedule and lesson predicate test the
actual assembled demonstrations.

**Rejected alternative.** Count witness frequency only. Frequency can be high while a cyclic
window still misses the needed branch.

**Probe.** `workspace/semantic_probe.py` reads the generator's declarations instead of
copying a rival-name list. At 100 lessons per band, no declared rival survived a lesson.

## D8 — Add an independent task-local probe

**Choice.** Keep `workspace/semantic_probe.py` as a reusable source-bound tool.

**Why.** The required battery semantic sample is intentionally small. The helper records the
sampler, generator/rule hashes, strict failures, unique inputs, dimensions, object counts,
witness counts, per-example rival disagreements, and surviving lesson windows.

**Usage.** From packet root with the runtime on `PYTHONPATH`, run the command recorded in
`RESULTS.json`. The retained final report is `checks/semantic_probe_100.json`.

## D9 — Tests were written against behavior before production replacement

The initial task-local test file was run against the selected baseline before rewriting the
generator. It failed 9 tests and passed 2 for the expected semantic, override, and lesson
contracts. After the single source replacement, the focused suite passed, and the final
portable task snapshot passed 11/11. This preserves a falsifiable red/green chain rather than
adding tests after the fact.

## Known limits

- dimensions are limited to 7..8 by 7..9;
- shapes come from a finite connected library fitting 3×3 placement slots;
- exactly two nonzero colors are used;
- component bounding boxes never overlap;
- all components are deliberately non-rectangular and rule-active;
- no degenerate or adversarial textures are advertised;
- the semantic probe measures declared rivals, not every possible human/model hypothesis;
- no claim is made about downstream training accuracy or masked solve success.
