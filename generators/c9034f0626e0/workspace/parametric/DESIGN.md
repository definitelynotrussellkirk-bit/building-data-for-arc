# Lattice-period prototype design

## Intent

Add a task-local, non-production prototype that varies one nearby rule parameter
while preserving the original family: a unique marker defines a row residue and a
column residue; matching background cells are painted with the marker color while
gray blockers and all other cells remain unchanged.

## Parameter contract

- Name: `lattice_period`
- Allowed values: `2`, `3`
- Original/default: `2`
- Sampling unit: chosen once per episode from a deterministic rule-only stream
- Canonical setting: period 2 must emit the canonical Racket source exactly
- Alternative: period 3 replaces the four coordinate remainders by modulus 3
- Input dependency: each retained grid must contain at least one zero cell whose
  period-2 and period-3 classifications differ, so the settings execute different
  transformations.

## Goals

Produce exact Racket programs, complete three-demo/one-query episodes for both
settings, masked public challenges, private labels/programs/counterfactuals,
query-rotation rival checks, same-input cross-setting evidence, hashes, runtime
receipts, focused tests, and a reproducible CLI.

## Non-goals and anti-goals

The prototype itself must not change the canonical rule, catalog metadata,
approval hashes, or shared runtime interfaces. Separate assignment-required
production repairs may (a) reject inputs that were never valid (`seed`
non-integers and invalid/negative `sample_index` values) and (b) reorder the
default marker-color curriculum while preserving the exact color domain, all
overrides, and rule semantics. Do not present the period-3 setting as approved.
Do not infer correctness from a Python mirror alone; execute both settings through
the included Racket verifier. Do not leak the hidden setting, program, or query
answer into public challenge files.

## Approaches considered

1. **Lattice period 2 versus 3 — selected.** Keeps the ordered pair of marker-derived
   coordinate residues and only changes lattice spacing. It is a small count
   parameter, creates strong same-input counterfactuals, and leaves color/blocker
   roles intact.
2. **Same versus opposite parity pair.** Nearby and viable, but changes the marker's
   relative phase rather than generalizing the coordinate-class concept; it also
   risks being learned as a simple inversion cue.
3. **Marker color versus fixed output color.** Easy to materialize, but weakens the
   marker's established output-color role and is closer to cosmetic reskinning.

## Production-gate addendum

The immutable before battery exposed 33 strict-scalar warnings: non-integer seeds
and non-integer or negative sample indices were accepted. The smallest repair is
call-domain validation at `generate` entry. It changes no valid call, grid, label,
Racket source, or parameter prototype behavior. Focused tests cover all reproduced
invalid scalars before the after battery.


## Production semantic-schedule addendum

The strict after policy found a measured lesson ambiguity even though every
named task-specific rival was refuted: the default color cycle placed all marker
colors below immutable gray-5 before all colors above gray-5. In one three-demo
window, a bounded `first_color_only` mutation fit every demonstration and failed
only on the query when the marker crossed from `<5` to `>5`.

The minimal curriculum repair keeps the same eight legal colors and exact
override behavior but alternates the default schedule around gray-5:
`(1, 6, 2, 7, 3, 8, 4, 9)`. Therefore every three-pair support drawn from any
cyclic four-pair window contains at least one marker below 5 and one above 5,
including every leave-one-query-out rotation. This changes default no-override
sampling order, not the transformation, domain, canonical authority, or labels
for a fixed input.

## Evidence limits

The retained run covers two settings, two episodes, eight inputs, eight query
rotations, and one declared rival per rotation. It does not prove uniqueness
against arbitrary programs, cover periods beyond 2 and 3, or grant production or
training approval.

## Native implementation plan — review-50fa7512499dcc0e

Reuse the two existing fixed-period programs and expose a three-value native
`lattice_rule` parameter. `ray_size` selects the first gray component hit strictly
to the marker's east, counts its four-connected cells, then chooses period 2 for
an even count or 3 for an odd count. This supplies an input-dependent intermediate
before the lattice operation can be selected. The canonical source remains exact.

Implementation is scoped to this home: add the thin adapter and promotion
contract, a constructive sampler/mirror, a standalone Racket resource, focused
native tests and a reusable bounded audit/export command. The sampler constructs
opposite-parity first and second demonstrations, supports 2–6 demos and 1–4
queries independently, and uses 9×9 through 30×30 meaningful scenes. The regular
training request is three demos/four queries. Two-demo episodes keep marker color
fixed across their queries to avoid an unsupported color-role switch; longer
lessons teach both sides of gray-5. Input randomness is independent of setting.

Verification order: missing-adapter test failure; native unit checks; protected
Racket label and finite-rival checks; exact-source inventory and native
qualification; protected wrong-intermediate witness; public projection and
rejection checks; final source review. Optional peers follow successful MAIN
qualification. Evidence is finite and reviewer-reported, with acceptance and
training admission left to their existing owner workflows. The ordered teaching
schedule does not claim arbitrary demo/query rotation closure.

### Self-review-driven refinement

Independent bounded review reproduced 38 fit-demos/disagree-query cases against
14 Python rival names; protected Racket confirmed eight ambiguous lessons in a
separate 21-episode sample. The root cause was accidental agreement of structural
features in short randomly assembled demonstrations. A fixed 64-candidate pool
per teaching slot now selects demonstrations by a finite coverage mask, never
by query labels. For 3+ demos selection is matched across settings; for 2 demos
it is setting-specific because rejecting the structural rivals for every
setting simultaneously is unnecessarily restrictive at that teaching budget.
The independent query stream remains matched and prefix-stable. Public export
also strips per-pair private fields and the retained legacy writer now uses exact
canonical visible-byte hashes. These changes repair demonstrated failures; they
do not claim universal induction or arbitrary rotation closure.
