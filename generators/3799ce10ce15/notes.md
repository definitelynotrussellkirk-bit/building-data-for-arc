# Working notes: 3799ce10ce15

## Reviewed repair

Baseline v1.3.1 had no `RULE_HASH`, exposed ignored/inaccurate controls, used
almost fixed geometry, placed one cell per present color, and had an
acceptance-only `self_check`. Version 2.0.0 preserves the canonical authority but
constructively varies canvas, legend size, frame count, frame geometry/layout,
presence patterns, and multiplicity.

The strongest canonical-fitting shortcut is a fixed-window parser: public examples
place legend colors at columns 2/5/8 and frames at three fixed boxes. The repair
registers that shortcut and an exactly-once-presence rival as executable
competitors. Every three-demo schedule window across all 12 cyclic starts and
three bands refutes both; the 100-lesson-per-band census found no ambiguity under
all four query rotations.

## Intentional bounds

- 13–18 rows and 18–25 columns
- 2–4 distinct legend colors
- 2–4 non-touching exact hollow frames
- nonempty frame interiors and at least two distinct presence rows
- uniform 1–3 copies for each present frame/color pair within a grid
- every generated legend color appears somewhere, although `self_check` accepts
  the canonical lawful case where one legend color is absent everywhere

These are curriculum choices, not claims that the Racket authority is undefined
outside them. Future widening should add named rivals and focused tests first.

## Retained evidence

The task-local suite is `tests/test_generator.py`. The independent parser/oracle,
rivals, distribution audit, and optional Racket parity runner are in
`workspace/reference_probe.py`. Root return documents contain exact before/after
commands, audit findings, solve exposure declarations, and evidence paths.
## Current reviewer considerations

Source SHA-256: `c88234b62a5bb2103984939a970e8ac94444303525216bc7f5bb0b789fc8fbce`.

# Decisions — 3799ce10ce15

## D1 — Preserve the authority; repair only the generator

**Decision.** Keep the canonical puzzle rows, Racket program, and labels byte-for-byte
unchanged. Pin the generator to canonical `RULE_HASH = "7962236ae928"`.

**Rationale.** Baseline Racket smoke and authority synchronization already passed.
The defects were in sampling, validation, metadata, and pedagogy, not the target
transformation.

**Alternative rejected.** Editing an archival raw-code mirror to remove catalog
divergence. It is not selected authority, execution parity already passes, and
changing it would broaden the review unnecessarily.

**Probe.** Before and after battery authority-set SHA-256 remains
`0ca6f4d5480835a69602f23e6d33f0fde3af43af4ae0a71589b43c3d38b89c1b`.

## D2 — Make every advertised axis exact and observable

**Decision.** Replace the baseline's ineffective surface with five strict axes:
`grid_h`, `grid_w`, `palette_size`, `n_frames`, and `copies_per_present`.

**Rationale.** These values affect pixels directly, admit finite legal ranges, and
can be reconstructed by `observe_overrides`. Exact controls make audit failures
reproducible and prevent silent requests from being ignored.

**Alternatives rejected.** A `texture` label or difficulty-only branch that could
not be recovered from a grid; probabilistic “best effort” dimensions; accepting
unknown override keys.

**Failure modes checked.** Every legal shared-tool cross-product, invalid types and
bounds, unknown keys, and each difficulty band. Final override audit accepted and
observed 20,430/20,430 draws with zero findings.

## D3 — Use exact hollow 9-components as the structural primitive

**Decision.** Detect each four-connected color-9 component, take its bounding box,
and require that the component equals the complete border of a rectangle at
least 3×3. Sort valid boxes lexicographically by top-left coordinate.

**Rationale.** This follows the canonical rule without relying on fixed windows or
frame dimensions. Equality to the expected border rejects broken, filled,
connected, and irregular pseudo-frames.

**Alternative rejected.** Searching for any rectangular 9 outline by scanning all
subrectangles. Component equality is simpler, deterministic, and prevents one
large connected component from being counted multiple times.

**Limitation.** Touching frames merge into one component and are therefore outside
the generated/validated grammar.

## D4 — Accept canonical legality, not curriculum preferences

**Decision.** `self_check` accepts all five canonical inputs, including an output
column whose legend color is absent from every frame. It validates types,
rectangularity, ARC bounds, legend distinctness, exact frames, body-color
membership/ownership, nonempty frame interiors, and at least two distinct
presence rows.

**Rationale.** A validator should follow authority semantics. Generated lessons may
be narrower, but lawful canonical inputs must not be rejected merely because the
curriculum prefers every legend color to appear.

**Rejected first attempt.** Requiring every legend color to occur somewhere. The
focused canonical test failed on a public demonstration, revealing that this was
a curriculum assumption rather than an authority invariant. That TDD failure is
retained in `checks/tdd-green/pytest-first.log`.

**Known limitation.** The generic `drop_minority_color` mutation sometimes remains
lawful, so 7/60 generic mutations are accepted. This is not hidden as a failure of
validation.

## D5 — Vary coarse geometry while retaining canonical support

**Decision.** Generate 13–18 rows, 18–25 columns, 2–4 legend colors, and 2–4 frames.
Frame exteriors vary over heights 4–5 and widths 4–6 and are packed into one or
two body rows and columns with random legal gaps/offsets.

**Rationale.** The baseline's fixed 5×6 rectangles and mostly fixed three-frame
layout allowed position and shape shortcuts. The chosen range supports several
layouts without rejection sampling and stays comfortably under ARC's 30×30 cap.

**Alternatives rejected.** Fully arbitrary rectangle packing, which adds search and
failure cases without teaching a new semantic distinction; retaining canonical
fixed boxes as a special generated profile, which would let hard-coded windows
survive some lessons.

**Probe.** `checks/independent-audit.json` observes ten input shapes and 475 distinct
frame boxes across 400 grids.

## D6 — Schedule a twelve-profile curriculum

**Decision.** Cycle deterministically through 12 tuples of
`(height, width, palette_size, frame_count, copies)`, offset by band. Residues 0,
4, and 8 use the canonical coarse profile 13×18/three colors/three frames with
copies 1, 2, and 3 respectively.

**Rationale.** A fixed schedule guarantees coverage in every short lesson and
makes every start auditable. Canonical-scale support appears in every band rather
than depending on chance.

**Alternative rejected.** Independent random axis draws. They can produce
three-example windows with no repeated-color evidence or no canonical-scale case,
and make ambiguity failures intermittent.

**Probe.** Task tests enumerate all 12 cyclic starts × three bands; 36/36 windows
refute all declared competitors. The shared 100-lesson-per-band census records
all accepted indices and query rotations.

**Limitation.** Difficulty names are keyed distribution bands, not a proven monotonic
human-difficulty scale.

## D7 — Build presence patterns constructively

**Decision.** Choose one nonempty nonfull bitmask, its complement, then additional
nonempty masks as needed. Shuffle the masks among frames.

**Rationale.** The first two masks ensure different output rows and complete legend
coverage without retry loops. Additional masks broaden combinations. Empty frame
interiors remain outside this curriculum.

**Alternative rejected.** Independent Bernoulli inclusion followed by repair. It
can collapse every frame to the same presence row or leave colors unexercised,
requiring opaque retries.

**Limitation.** Every generated legend color appears somewhere, though canonical
validation allows absent colors. Future widening should schedule absent-color
profiles explicitly and add rivals for them.

## D8 — Separate presence from multiplicity

**Decision.** Repeat every present frame/color pair one, two, or three times,
uniformly within a grid; expose that count as an exact axis.

**Rationale.** Baseline examples with exactly one cell per present color allow a
single-pixel or exactly-once shortcut. Multiplicity two and three force the output
to depend on `count > 0`, not `count == 1`.

**Alternative rejected.** Arbitrary independent counts per frame/color. It would
broaden coverage but make the requested `copies_per_present` override impossible
to observe exactly. A future `multiplicity_mode` axis could add that safely.

**Probe.** The `exactly_once_presence` rival disagrees on 266/400 independent grids
and is refuted in every generated lesson window.

## D9 — Declare the strongest canonical-fitting shortcut executable

**Decision.** Implement `fixed_canonical_windows`, which reads legend columns
2/5/8 and the three public frame boxes. Register it as a semantic rival,
canonical shortcut, lesson competitor, and witness target.

**Rationale.** It fits all five canonical pairs and is a plausible memorization
strategy. A curriculum should actively demonstrate that legend/frame positions
are structural, not absolute.

**Probe.** `checks/question/fixed-window-witness.json` uses a 13×18, three-color,
three-frame generated input so the rival cannot be dismissed as merely a size or
count mismatch. Canonical Racket and the independent intended-rule mirror agree;
the rival differs in five cells. It also differs on 400/400 independent generated
inputs.

## D10 — Require lesson-level, not only pair-level, evidence

**Decision.** Use three demonstrations plus one query. `lesson_identifiable` first
checks grammar and labels, then rejects a lesson when any declared competitor fits
all demonstrations but predicts a different query output.

**Rationale.** Correct individual labels do not guarantee a teachable bundle.
Three examples match the task's export contract and permit complementary schedule
profiles to appear together.

**Probe.** The shared census materialized 300 lessons and held out every pair once:
1,200/1,200 rotations had no declared-rival ambiguity. Task tests additionally
cover all cyclic schedule starts, which the shared census does not enumerate.

**Limitation.** Passing named rivals is not universal program induction.

## D11 — Add an independent task-local probe

**Decision.** Put parsing, intended output, rival implementations, distribution
checks, and optional Racket comparison in `workspace/reference_probe.py`; tests
import this probe rather than generator helpers.

**Rationale.** A test that reuses the production parser can reproduce the same bug.
The probe gives later agents a compact executable audit surface and can run in the
portable task-test snapshot.

**Probe.** 53/53 real Racket comparisons passed; canonical Python output matched
5/5 pairs; no self-check errors or nondeterminism occurred in 400 generated grids.

## D12 — Follow TDD and retain the failure evidence

**Decision.** Write focused tests against the frozen baseline, record their
expected failures, then implement the minimal coherent repair and rerun the same
suite.

**Rationale.** The red run proves the tests detect the original defects rather than
merely documenting the final implementation.

**Evidence.** `checks/tdd-red/pytest-red.log` reports 32 failed/16 passed on the
baseline. The original repair suite reached 84 passes; an additional portability regression first failed in `checks/tdd-red/pytest-portable-red.log`, then the final copied-runtime stage passed 85/85 in `checks/task-tests-final/result.json`.

## D13 — Keep solve exposure declarations literal

**Decision.** Finish the pre-repair task as blind (`earlier exposure: no`) and the
post-repair selected task as exposed (`earlier exposure: yes`), both with no
reference consultation during solving.

**Rationale.** Repair work necessarily disclosed the selected task's rule. Calling
the later solve blind would overstate its evidentiary value.

**Limitation.** Visible-example checks do not reveal masked-query correctness.

## D14 — Audit unrelated targets without editing them

**Decision.** Produce exact, source-bound counterexamples for `376e5d08bb1c` and
`b58ebf4ada2f`, but leave their source unchanged.

**Rationale.** The assignment requests adversarial findings, not cross-task repair.
Keeping them separate avoids accidental scope expansion and makes the selected
patch routine to apply.

**Evidence.** `AUDIT.md` and `checks/audit/*/evidence.json`.
