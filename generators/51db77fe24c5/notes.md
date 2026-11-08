# Working notes: 51db77fe24c5

The 2026-10-04 review replaced imported generator `1.2.0` with semantic sampler
`2.0.0`; the selected Racket authority was not changed. The old sampler exposed
only three finite distractor masks, accepted unknown controls, advertised dead or
overlapping axes, and did not pin its rule hash.

The repaired grammar always includes witnesses against three especially plausible
wrong rules: memorize the old masks, recolor every object with a 2×2 bounding box,
and recolor every four-cell object. A separately sampled broad distractor prevents
the negative class from collapsing to those controls. The finite declared-rival
set is evidence against named shortcuts, not a proof of universal identifiability.

Reusable independent probes live in `workspace/reference_probe.py`. The return's
`DECISIONS.md` records rationale, alternatives, measurements, and residual limits.
Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `c8d5e3cbf5d570bb4037f3d64971b863fbced3e3f76fe45cbeeb7bac842290b6`.

# Decisions — 51db77fe24c5

## D1 — Preserve the canonical transformation and replace only the sampler

**Choice.** Keep the selected Racket rule unchanged and pin its canonical hash
`06fb2695c6fe` in generator `2.0.0`.

**Rationale.** The before `rule_smoke` and authority checks passed, canonical examples
matched an independent component oracle, and the defects were in distribution and
control semantics rather than the transformation.

**Alternatives rejected.** Rewriting the Racket source would add authority risk without
fixing the finite-mask curriculum. Broadening the conceptual rule to any 2×2 bounding
box would be wrong for three-cell L objects.

**Probe.** Canonical-pair oracle test, Racket rule smoke, authority sync, and unchanged
shared-source byte comparison.

**Failure modes / limits.** Archival raw code remains textually divergent, as it did in
the baseline; selected execution parity passes. The generator's Python mirror is a test
oracle, not a replacement authority.

## D2 — Advertise only four controls that are exact and pixel-observable

**Choice.** Expose `grid_h`, `grid_w`, `square_count`, and `distractor_kind`; delete
palette, texture, density, and alias controls whose requested values were not distinct
or exact.

**Rationale.** An axis is useful for dataset construction only when a caller can request
it, observe it in the emitted sample, and replay it. The baseline advertised eight-ish
controls but produced 13,940 override findings in 50,400 draws.

**Alternatives rejected.** Keeping compatibility aliases would preserve silent behavior
and make exact dataset stratification unreliable. Declaring incompatibility matrices
was unnecessary because every legal tuple can be constructed on the minimum 8×8 grid.

**Probe.** `observe_overrides`, 54 focused tests, central override gate, and the
5,880-call full joint-axis sweep.

**Failure modes / limits.** The four controls do not expose target positions or exact
polyomino masks. That is deliberate: those remain keyed stochastic variation rather
than promises requiring exact observation.

## D3 — Use full-domain defaults with difficulty weighting, not band-restricted axes

**Choice.** All bands retain exact support for every 8–14 dimension, 1–2 target count,
and five distractor kinds; difficulty changes only default weights.

**Rationale.** Exact overrides should have one domain independent of band. Weighting
still lets easy favor smaller canvases/one target and hard favor two targets/richer
polyominoes.

**Alternatives rejected.** Hard range 9–14 initially seemed reasonable but failed the
pinned canonical-profile floor by starving 8–10 support. Separate per-band validity
ranges would make joint controls surprising and harder to stratify.

**Probe.** Pinned 20-draw profile-floor regression and central profile-floor report.

**Failure modes / limits.** Difficulty is a soft distribution label, not a monotone
complexity guarantee for every individual draw.

## D4 — Put a 2×2-bounding-box L control in every input

**Choice.** Always include one of three L-triomino orientations absent from the old
three-mask support.

**Rationale.** `bbox_2x2` fits all 3 canonical pairs, so random occurrence is not enough;
every complete lesson needs a direct negative witness. This same object also breaks the
historical three-mask memorizer.

**Alternatives rejected.** Merely adding vertical lines and T shapes increases diversity
but does not distinguish “solid square” from “2×2 bounding box.” Making the L optional
would allow short lessons where the rival survives.

**Probe.** `bbox_2x2_nonsquare` witness, `legacy_mask_memorizer` rival, focused fixture,
semantic gate, and 300-lesson census.

**Failure modes / limits.** A mandatory L is a visible curriculum regularity; a learner
could treat it as a fixed negative token. The independently sampled broad distractor
prevents it from being the whole negative class.

## D5 — Put a non-square four-cell zigzag control in every input

**Choice.** Always include the connected mask `((0,1),(0,2),(1,0),(1,1))`.

**Rationale.** A late adversarial review found that lessons without a four-cell
nonsquare were fit by “recolor every four-cell component.” The initial green gates did
not declare or test that rival.

**Alternatives rejected.** Depending on optional `line4`/`t4` broad draws would refute
the shortcut only sometimes. A disconnected four-cell control would change the object
model and be less directly comparable to the target.

**Probe.** Source-bound failing regression before the fix, `size4` rival and witness,
600-draw semantic gate, and final 300-lesson census.

**Failure modes / limits.** The fixed orientation is regular. Rotating it would add
surface diversity, but exact observation and current minimum-grid packing are simpler;
the semantic distinction is already explicit.

## D6 — Add one broad distractor from open and closed families

**Choice.** Add exactly one broad distractor selected from domino, line3, line4, four T
orientations, or a grown connected 5–8-cell polyomino inside 4×4.

**Rationale.** The baseline's three fixed masks made memorization sufficient. Growth
creates a large support while retaining reliable packing on 8×8. Lines and T shapes
also restore canonical negative profiles missing from the imported sampler.

**Alternatives rejected.** A larger finite hand-written catalogue still invites mask
memorization. Unbounded random walks can create large, thin masks that make exact joint
placement unreliable at minimum dimensions.

**Probe.** 96 draws per named kind, minimum distinct-mask floors, 320-draw default
coverage (at least 80 negative masks and 300 unique inputs), and the exhaustive axis
sweep.

**Failure modes / limits.** Polyominoes are bounded to 4×4 and 5–8 cells; the conceptual
negative domain is much larger. The one-broad-distractor policy also caps object-count
variation.

## D7 — Constructively place all shapes with backtracking and an orthogonal halo

**Choice.** Enumerate legal placements, shuffle them with keyed randomness, and
backtrack until every requested component is placed without overlap or orthogonal
contact.

**Rationale.** Silent retries/drops would make `square_count` and `distractor_kind`
untruthful. Separation ensures object identity is unambiguous under four-connectivity.

**Alternatives rejected.** Independent rejection placement can fail or bias cramped
8×8 joint requests. Expanding the grid after failure would violate exact dimensions.

**Probe.** 5,880 legal joint requests at the minimum and full dimension ranges; zero
placement failures. `observe_overrides` confirms the realized tuple.

**Failure modes / limits.** Backtracking could become expensive if future edits add more
or larger shapes. Current worst observed call in the final sweep was under 0.1 seconds.

## D8 — Keep structural validity separate from teaching guarantees

**Choice.** `self_check`/`strict_canonical_like` require a lawful binary grid with at
least one square and one nonsquare. Mandatory curriculum controls are declared through
witnesses and rival contracts rather than making canonical inputs fail validation.

**Rationale.** All canonical inputs must remain valid even though they lack every new
teaching control. Conflating source-domain validity with the stronger generated lesson
contract would reject legitimate examples.

**Alternatives rejected.** Requiring the fixed L and zigzag in `self_check` would make
canonical acceptance impossible. A permissive checker without semantic hooks would
repeat the baseline's `NO_CONTRACT` weakness.

**Probe.** Three canonical inputs accepted; malformed/empty inputs return diagnostics;
semantic witnesses fire on generated draws; lessons are separately scored.

**Failure modes / limits.** External callers can supply a structurally valid but weak
lesson. Dataset admission must run the semantic/lesson gate, not only `self_check`.

## D9 — Declare a small executable rival library and retain an independent probe

**Choice.** Declare five named rivals (`legacy_mask_memorizer`, `bbox_2x2`, `size4`,
`all_blue`, `identity`) and add `workspace/reference_probe.py` that does not import the
production helper implementation.

**Rationale.** Executable wrong rules turn vague “diversity” claims into falsifiable
lesson-level checks. The independent probe reduces the chance that tests merely repeat
production code.

**Alternatives rejected.** Relying only on aggregate uniqueness or marginal profile
coverage would not catch the baseline memorizer or the audited bounding-box shortcut.
A universal program search is too expensive for routine generator intake.

**Probe.** Semantic gate, task-local tests, 300-lesson census, and final exposed solve.

**Failure modes / limits.** The rival set is finite and reviewer-authored. It cannot prove
that Qwen3.5-9B will infer the intended abstraction or that no undeclared shortcut
exists. This directly motivates `QUESTION_ANSWER.md` and feedback F1.
