# Working notes: cae2423a6477

## Authoritative rule

The Racket rule was retained unchanged. It recolors a green component exactly
when the component equals the border of its own rectangular bounding box. The
Python `rule_mirror` remained in parity with that authority on all 120 official
after-check samples.

## Prior review: version 2.0.1 to 3.0.0

The preceding accepted review replaced a broad set of inert or aliased axes
with one exact `scene_profile` axis, added deterministic profile scheduling,
structural self-checks, semantic hooks, and three profiles:
`canonical_small`, `large_open`, and `hollow_irregular`. In version 3.0.0 the
hollow negative was a rectangular ring with one outward nub. That object
correctly refuted the declared “any object with a hole” rival.

## Current review: version 3.0.0 to 3.1.0

### Baseline finding

The official before battery was fully green (12/12 stages), but it only tested
rivals already declared by the generator. An independent object-feature probe
found an undeclared canonical-fitting shortcut:

> Recolor every closed, unbranched, one-cell-wide loop.

All public pairs are consistent with this shortcut. The version 3.0.0 nubbed
ring has a branch, so the shortcut correctly leaves it green; consequently it
also fit all 300 sampled complete baseline lessons across easy, medium, and
hard bands.

A first replacement with only a stepped simple loop refuted that shortcut but
exposed the complementary shortcut “recolor every object with a rectangular
hole.” The final design therefore triangulates the target with two different
hollow negatives rather than exchanging one blind spot for another.

### Implemented distribution

- Kept `canonical_small` and `large_open` unchanged.
- Changed `hollow_irregular` to contain both:
  - one stepped, non-rectangular, closed unbranched loop; and
  - one exact rectangular ring with a single outward leaf cell.
- Retained at least one true rectangular frame in every grid.
- Retained the three-example residue schedule, one-cell diagonal moat, fixed
  profile dimensions, keyed randomness, and exact override observability.
- Added enclosed-hole extraction, rectangular-hole recognition, and exact
  recognition of the nubbed-ring family.
- Added `closed_unbranched_loop` and `rectangular_hole` semantic rivals and
  bound both to the hollow witness profile.
- Bumped the generator version to `3.1.0`; the rule hash stayed unchanged.

### Tests and review utility

- Added regressions proving that both new rivals fit every canonical pair but
  are refuted by every sampled three-example lesson.
- Strengthened hollow-profile assertions to require both complementary decoys.
- Reworked one destructive-row mutation test to use 60 seeds per band and a
  measured 90% rejection floor. A universal assertion was invalid because a
  destructive row copy can occasionally map one supported tiny decoy to a
  different supported tiny decoy.
- Added `workspace/rival_probe.py`, an independent low-complexity rival miner.
  On the frozen version 3.0.0 baseline it reports the closed-loop rival alive
  in 300/300 sampled lessons. On version 3.1.0 all five tested
  canonical-fitting rivals survive 0/300 lessons.

## Verification

- Task-local tests: 22 passed (21 generator regressions plus the rival-probe
  regression).
- Custom stress: 2,700 generated grids and 900 complete lesson windows, zero
  generation, self-check, observability, or rival-survival errors; 2,697 grids
  were byte-distinct.
- Official after battery: all 12 stages green, including Racket rule smoke,
  semantic gate, profile floor, override contract, grammar, and authority sync.
- Rule smoke: 120/120 applications fired, 120 distinct outputs, and 120/120
  Python-mirror parity.
- Standalone generator lint: pass.
- Repository suite: 104 passed, 28 skipped by pytest because those unit tests
  require a host-visible Racket runtime. The packet battery used its bundled
  Racket runtime and passed the Racket stages.

## Limitations

The rival probe searches a deliberately small, interpretable grammar of
object-level rules. It is evidence against common shortcuts, not a proof that
no more complex rival exists. The lesson geometry remains fixed to isolated
color-3 objects on black because changing palette, connectivity, or object
interaction would alter the task rather than clarify the existing rule.
## Current reviewer considerations

Source SHA-256: `7649796866c1ece02ee1c08119468a251f20deaead1196328e57b1d0a6de32d5`.

# Decisions — cae2423a6477

## Rule and authority

| Choice | Original rationale | Alternatives considered | Probe/evidence | Failure modes and limitation |
|---|---|---|---|---|
| Keep the Racket rule unchanged. | The inherited authority exactly checks whether a color-3 component is the complete border of its own bounding box. | Rewrite the rule, change the canonical wording, or broaden “ring” to any hollow object. | Canonical parity passed; before and after rule-smoke each passed, and the after run matched the Python mirror on 120/120 generated inputs. | The authority does not itself establish that the demonstrations identify the rule; that is a generator responsibility. |
| Keep `RULE_HASH = 1f6f97325987`. | The rule source did not change. | Bump the hash merely because the curriculum changed. | Authority sync and Racket lint passed. | Hash stability is correct only because no rule bytes changed. |
| Bump generator version from `3.0.0` to `3.1.0`. | Generated inputs and semantic contracts changed while the rule did not. | Keep `3.0.0`, or make a major bump. | Determinism tests use the new versioned keyed stream; all checks passed. | Existing seeds intentionally produce different grids under the new version. |

## Input-distribution choices

| Choice | Original rationale | Alternatives considered | Probe/evidence | Failure modes and limitation |
|---|---|---|---|---|
| Preserve black (`0`) background and green (`3`) foreground. | These colors are invariant in the canonical task and the output operation is a selective recolor to orange (`7`). | Palette randomization. | Canonical examples and authority are color-specific; every stress grid passed self-check. | This does not teach color abstraction, intentionally. |
| Preserve isolated 4-connected objects with a one-cell diagonal moat. | Object identity must be unambiguous; the prior review introduced the moat to prevent accidental mergers. | Allow touching, diagonal contact, or overlapping decoys. | 2,700 stress draws passed component/profile recovery. | It does not train segmentation under contact; that would add a separate difficulty axis and could change the rule interpretation. |
| Keep one exact semantic axis, `scene_profile`. | The preceding review removed inert and aliased axes. A profile names a real, recoverable object mixture. | Add separate booleans for each decoy, geometry, or transform. | Override gate accepted 360/360 cases with exact observations and rejected an unknown key. | One axis offers less arbitrary combinatorial variation, but avoids dishonest controls. |
| Keep the three-example residue schedule. | Three examples are enough to place one canonical-like scene and both major contrastive families in every consecutive lesson. | Random profile choice; increase `EXAMPLES_NEEDED`; combine everything in every demo. | All 900 stress lesson windows covered every profile and passed `lesson_identifiable`. | The guarantee depends on sequential sample indices, as documented by `schedule_profile`. |
| Keep `canonical_small`. | It anchors the generated distribution near public dimensions and frame geometries. | Remove canonical-like examples and use only adversarial scenes. | Profile-floor gate passed in all bands; all canonical inputs pass `strict_canonical_like`. | This profile alone remains ambiguous, so it must not be sampled as the whole lesson. |
| Keep `large_open` as one-gap rectangular borders. | It directly refutes size and bounding-box threshold shortcuts while staying visually close to positives. | Use arbitrary large blobs, solid rectangles, or many missing border cells. | `size_at_least_8` and `bbox_at_least_3x3` survive 0/300 sampled lessons. | A single-gap border targets the most local near-miss; it does not enumerate every open shape. |
| Replace the single hollow negative with two complementary hollow negatives. | The old nubbed ring refuted “any hole” but allowed “closed unbranched loop.” A stepped loop alone then allowed “rectangular hole.” | Keep only the nub; keep only the stepped loop; use a thick irregular donut; add a fourth profile. | Frozen baseline: loop rival survived 300/300 windows. Final generator: loop, rectangular-hole, and any-hole rivals each survived 0/300. | Two objects increase scene density and placement complexity; stress testing found no placement failures. |
| Use a stepped one-cell-wide loop with height ≥4 and width ≥5, randomized shoulder, reflection, and rotation. | It is a simple closed cycle that is visibly non-rectangular and has an irregular enclosed region. | Concave thick rings, diagonally connected loops, or a fixed single shape. | Every hollow draw had one `hollow_irregular`; the loop rival disagreed with the authority. Transform variants passed profile recovery. | The family is still one topology and may not refute more elaborate shape predicates. |
| Retain a rectangular frame plus one outward leaf cell. | It preserves a rectangular enclosed hole while making the foreground fail exact-frame equality. | Inward spur, two nubs, detached marker, or a thickened side. | Every hollow draw had one `nubbed_rectangular_hole`; the rectangular-hole rival disagreed with the authority. | A one-cell branch is a narrow near-miss, chosen for clarity rather than exhaustive morphology. |
| Keep optional canonical small decoys in medium/hard scenes. | They preserve continuity with public negative objects and add object-count variation. | Remove them or make them mandatory. | Profile classifier explicitly allows them; stress and override checks passed. | Optionality can create occasional byte-level duplicates; 2,697/2,700 stress grids were distinct. |
| Keep true-frame counts and size ranges from version 3.0.0. | They already covered canonical sizes and progressively larger valid frames without a demonstrated defect. | Increase maximum size, add 1-cell-thick degenerate “frames,” or force two positives everywhere. | Profile-floor, diversity, rule-smoke, and custom stress passed. | Very large frames and thickness variants remain outside the intended exact-border task. |
| Keep existing profile canvas dimensions. | The added object might have required larger canvases, but changing dimensions would reduce canonical proximity. | Enlarge hollow canvases preemptively. | 900 hollow-profile stress draws across bands placed all required objects with zero restart exhaustion. | The 40-restart placer is empirically supported, not mathematically proven for every future geometry change. |

## Analysis and validation choices

| Choice | Original rationale | Alternatives considered | Probe/evidence | Failure modes and limitation |
|---|---|---|---|---|
| Refactor hole counting into `_enclosed_holes`. | The new rectangular-hole distinction requires hole geometry, not only a count. | Duplicate flood-fill logic in a second predicate. | Existing and new tests pass; official lint and self-check pass. | The analysis is 4-connected and bounded to each object's bbox, matching the task's object semantics. |
| Recognize nubbed rings by removing one degree-1 cell and testing the remainder as an exact frame. | This is an exact structural description of the emitted family. | Identify by size formula or by “rectangular hole plus branch.” | Profile observability remained exact across 2,700 stress draws. | The classifier intentionally rejects other branched rectangular-hole objects. |
| Declare both new rivals and bind them to `hollow_irregular_counterexample`. | Declared rivals make the official semantic gate enforce the distinction. | Rely only on bespoke tests or the external probe. | After semantic gate reports all five competitors declared and zero survivors. | Declared lists can still omit unknown rivals, motivating the independent probe. |
| Add an independent `workspace/rival_probe.py`. | The baseline passed the official gate precisely because the problematic rival was undeclared. | Add only another declared rival; manually inspect examples. | The tool fails on the frozen baseline and passes on the selected generator in an automated regression. | Its candidate grammar is finite and task-specific; it is a prototype for a broader gate, not a completeness proof. |
| Change the row-copy mutation regression to broad measured sampling and a 90% floor. | Five seeds produced unstable applicability, and some edits legitimately map one supported tiny decoy to another. | Demand 100% rejection; delete the test; forbid valid small-decoy transformations. | Across 180 deterministic seeds, the revised test has sufficient applicable cases and passes. | A statistical floor detects regression in aggregate rather than guaranteeing rejection of every individual mutation. |

## Stopping decision

I stopped after the source-bound target had: (1) explicit regressions for both
newly discovered shortcuts, (2) a reusable independent probe that fails on the
frozen baseline and passes on the selected source, (3) zero errors in 2,700-grid
stress and 900 lesson windows, (4) all 12 official after stages green, and (5)
the full repository suite green under the correct import path. Further work
would broaden the rival grammar rather than address a demonstrated defect in
this generator.

## Proposed native selected-barrier family

The separate `workspace/parametric/` proposal preserves production version
3.1.0 and generator SHA-256
`7649796866c1ece02ee1c08119468a251f20deaead1196328e57b1d0a6de32d5`.
Its default `completion_mode=border` returns the exact canonical program.
`completion_mode=enclosed` first paints exact 4-connected green rectangular
outline components orange, then uses only those orange cells as barriers for
global four-neighbor exterior reachability. It paints unreachable zeros red
and preserves detached green contents. Diagonal frame contact may collectively
enclose cells outside every individual frame bounding box. This extends the
proposed input grammar beyond the production sampler's diagonal moat without
changing canonical object connectivity.

The constructive two-demo basis includes wide and tall boundary-spanning
frames, nested frames, green contents, collective pockets, open/irregular
loops, inward/outward branches, thin and solid shapes, and a same-perimeter
geometry spoof. The 29×29 core example incurs a deliberate context cost.
Independent RNG streams supply 2–6 demonstrations and 1–4 novel queries up to
30×30, with matched inputs across settings and stable count prefixes.

Current source-bound evidence is in
`workspace/parametric/evidence/current/summary.json` and the native inventory.
The bounded audit passed 80 episodes, 640 independent labels, 2,720
rival/lesson combinations and 258 protected executions; portable task tests
passed 91/91. The finite bank has 28 border names and 40 enclosed names, with
39 observed enclosed signatures because bbox-only and eight-neighbor filling
coincide on current controls. These results do not prove universal inference
or all-seed success. Native qualification, protected causal replay and public
projection checks support review; owner exact-source acceptance and training
admission remain separate decisions.
