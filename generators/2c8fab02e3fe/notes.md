# Current account: 2c8fab02e3fe

## Intended rule

Color 8 forms one complete hollow rectangular frame. Exactly one non-{0,8}
color occurs once; that singleton key lies outside the frame. Fill every strict
interior cell of the frame with the singleton key color, overwriting any lawful
interior distractor, while preserving the frame and all outside cells. The
selected canonical Racket authority is unchanged and pinned by
`RULE_HASH = 716ceab8f6ca`.

## Baseline findings and prior evidence used

The selected 1.2.1 baseline had no rule pin, inert or unprobeable controls,
ordinary/negative texture overlap, and a validator that accepted four
disconnected color-8 bounding-box corners as a frame. Its clean-only lessons
also left two canonical-fitting shortcuts alive: choose the most frequent
non-frame color, or paint only zero interior cells.

The prior return used only as a lead was `review-dc30427a56c13c3f:v0001`
(`zip_sha256=62bfdc9a69e20dd15970eeaff36c67f32cf5b9fe1f90cc24a214dc0bbe719f6a`),
bound to baseline generator SHA-256
`5ef1a0a2c57ec55d2e5725b1dbcb00359ea936d6d2a44cc581b87ee35c50c85b`.
This review independently reproduced the defects. The minimal validator
reproducer is
`counterexamples/review-dcabda7bc8743208-validator-corner-dots.json`.

## Reviewed design (2.2.0)

The exact visible controls are:

- `grid_h` 8..16 and `grid_w` 10..18;
- `frame_h` 4..7 and `frame_w` 4..9;
- `key_color` in 1..7 or 9;
- `key_side` top/right/bottom/left;
- `decoy_mode` clean/outside_pair/inside_pair/split_pair.

Every legal joint combination is constructive. Unknown controls, wrong types,
booleans supplied as integers, invalid difficulties, and out-of-range values
are rejected. `self_check` requires the color-8 set to equal one complete
rectangular perimeter of at least 4×4, exactly one outside singleton key, and at
most one repeated decoy color in the declared location class.

Three demonstrations are drawn from a four-pair cyclic curriculum. Every four
consecutive pairs contain all four key sides and all four decoy modes. Separate
seed-derived phases for color, side, decoy role, and geometry prevent a fixed
side→color or profile→color lookup from solving the task. Repeated colors refute
frequency selection; inside and split pairs refute preserving pre-existing
interior cells. Non-five keys, non-square frames, keys not below the frame, and
seed-phased side/color combinations refute four more declared competitors.
The retained Racket-labelled witness is
`counterexamples/review-dcabda7bc8743208-rival-witness.json`.

A self-review caught an intermediate 2.1.0 confound in which schedule slot,
key side, key color, decoy role, and geometry were still correlated. That design
was not retained. The final 2.2.0 schedule independently phases these roles and
adds the executable `old_side_color_lookup` rival plus a focused deconfounding
regression. A second regression caught an intermediate canonical-profile drop
to 11/60; the final phase and selected hard profiles restore 15/60 without
reintroducing the role correlation.

## Measured final-source evidence

Generator SHA-256:
`c2032b904c771f4d78f366cd6095fac997257af357e6073f22a4982676f5ba6c`.

- Focused and portable task tests: 29/29 passed.
- Required-rotation semantic gate: 600/600 strict draws; 4/4 canonical inputs
  accepted; six witnesses and six declared competitors exercised; 12/12
  three-demonstration lessons identifiable; 0/48 ambiguous held-out rotations.
- Canonical profile floor: 15/60 exact and envelope hits, with easy 7/20,
  medium 3/20, and hard 5/20; no canonical input rejected.
- Compact exact-control matrix: 77,400/77,400 accepted draws across 860 cases,
  with zero findings.
- Production census: 300/300 four-pair lessons, 1,200 labelled pairs, zero
  ambiguous production lessons, 0/1,200 ambiguous query rotations, and 1,194
  byte-unique inputs.
- Task-local exhaustive probe: 512 joint endpoint combinations, 192 cyclic
  lesson windows, and 768 held-out query rotations, all passing.
- Exposed final-source solve: 3/3 visible demonstrations passed on revision 1.

## Decisions reversed

The baseline palette aliases, singleton metadata axes, and texture labels were
removed rather than renamed because their values were byte-identical, invalid,
or not exactly observable. Bounding-box inference was replaced with exact frame
perimeter validation. Clean-only lessons were replaced with lawful repeated-pair
and overwrite witnesses. The first repaired fixed-profile schedule was then
replaced with seed-phased roles after a self-review showed that visible side and
geometry could proxy the key color.

## Limits and open questions

The sampler intentionally covers one complete frame and at most one repeated
color pair; it does not claim every input the raw Racket program can execute on.
Identifiability is finite evidence against six declared plausible competitors,
including two that fit every canonical pair, not a proof against every possible
hypothesis. Frame color 8 and background 0 remain fixed canonical roles. No
Racket authority or canonical data changed.
## Current reviewer considerations

Source SHA-256: `c2032b904c771f4d78f366cd6095fac997257af357e6073f22a4982676f5ba6c`.

# Decisions — 2c8fab02e3fe

## D1 — Preserve the canonical rule and fixed semantic colors

**Original choice/rationale.** The canonical task fixes background 0 and frame
color 8. The baseline gave no reliable reason to reinterpret these as
interchangeable roles.

**Decision.** Keep the selected Racket authority unchanged, pin its normalized
hash `716ceab8f6ca`, and vary only the singleton key among 1..7 and 9.

**Alternatives rejected.** Permuting frame/background colors would create a new
task unless each permutation were separately shown lawful by the authority.
Changing the Racket rule was unnecessary because all four canonical pairs and
the intended transformation already agree.

**Probe and limits.** Authority sync, rule smoke, four canonical-pair tests, and
the Racket-labelled retained witness all pass. This deliberately does not claim
color-role interchangeability.

## D2 — Replace descriptive texture labels with exact visible controls

**Original choice/rationale.** Baseline metadata exposed broad textures and
metadata-like controls, but several values were inert, invalid, overlapping, or
unobservable. The original rationale was otherwise undocumented.

**Decision.** Expose only `grid_h`, `grid_w`, `frame_h`, `frame_w`, `key_color`,
`key_side`, and `decoy_mode`. Each value is exactly recoverable from pixels.
Unknown keys, invalid types, booleans masquerading as integers, and out-of-range
values raise errors.

**Alternatives rejected.** Renaming dead controls would preserve the same defect;
probabilistic “preferences” would not satisfy exact override semantics.

**Probe and limits.** The shared compact matrix covers 860 cases and 77,400
draws; the task-local probe enumerates all 512 joint endpoint combinations. The
sampler intentionally supports one frame and at most one repeated pair, not all
raw programs accepted by the Racket evaluator.

## D3 — Validate exact frame geometry

**Original choice/rationale.** Baseline `self_check` inferred a frame from the
bounding box of color-8 cells. That is easy to implement but accepts disconnected
corner dots.

**Decision.** Require the color-8 set to equal the complete perimeter of one
rectangle of at least 4×4. Require one non-{0,8} singleton outside the bbox and
at most one repeated decoy color in a lawful location pattern.

**Alternatives rejected.** Merely checking four corners or bbox dimensions leaves
the same hole. Flood-fill connectivity alone would still admit nonrectangular
loops.

**Probe and limits.** The retained corner-dot JSON is accepted by the baseline
and rejected by the repair; all four canonical inputs remain accepted. Extra
color-8 interior marks are outside this documented training domain even if the
raw program could execute on them.

## D4 — Teach singleton selection and destructive overwrite

**Original choice/rationale.** Baseline examples had empty interiors and only one
non-frame color, so choosing the most frequent color and preserving existing
interior cells both fit every canonical pair.

**Decision.** Schedule `clean`, `outside_pair`, `inside_pair`, and `split_pair`
examples. Repeated decoy colors force selection by singleton count; inside/split
pairs show that the whole strict interior is overwritten.

**Alternatives rejected.** Adding random noise without an executable rival test
could increase visual diversity while leaving the same shortcut. A single fixed
counterexample would not guarantee every three-demo rotation contains enough
evidence.

**Probe and limits.** Six witnesses map to six executable competitors. The shared
smoke test checks 12 three-demo lessons and 48 query rotations; the larger census
checks 300 lessons and 1,200 rotations; the task-local probe checks 192 cyclic
windows and 768 rotations. Passing a finite competitor set is not a proof against
all conceivable rules.

## D5 — Seed-phase roles instead of fixing them to profile slots

**Original choice/rationale.** The first repair used fixed profile slots to make
coverage inspectable. Self-review showed this also made side and geometry a proxy
for key color.

**Decision.** Independently phase key color by `seed//4`, decoy role by `seed//2`,
key side by `seed`, and geometry by cyclic slot. Every four consecutive pairs
still cover all sides and decoy roles, while cross-seed lessons break fixed
side→color and geometry→color mappings.

**Alternatives rejected.** Pure random choice could miss a required teaching role
inside a short lesson. Keeping the fixed schedule and merely adding one witness
would leave production examples correlated.

**Probe and limits.** A test over 32 seeds verifies each side sees all eight key
colors and all four decoy modes, and each geometry sees at least four key colors.
The `old_side_color_lookup` competitor is now declared and refuted. This tests the
known proxy family, not every possible high-order correlation.

## D6 — Restore profile support after deconfounding

**Original choice/rationale.** Independent phasing changed which pinned samples
were clean; only clean samples have the canonical three-color profile. The first
version fell from a green floor to 11/60.

**Decision.** Use the independent `seed//2` decoy phase and return selected hard
slots to canonical dimensions, retaining one broad hard slot. This yields 15/60
exact hits without coupling decoy mode to key color or side.

**Alternatives rejected.** Duplicating the clean mode would weaken overwrite
coverage under some held-out rotations. Faking a three-color decoy would violate
the singleton/frame domain. Opting out of the profile gate was unjustified.

**Probe and limits.** The regression was written and observed failing at
`{'easy': 6, 'medium': 4, 'hard': 1}`. Final official counts are easy 7, medium
3, hard 5. Hard therefore still includes broad-scale examples, but its default
scale diversity is intentionally bounded.

## D7 — Require arbitrary query rotations

**Original choice/rationale.** A four-pair schedule with three demonstrations can
be assembled with any one pair held out. Ordered-only validation would certify a
lesson that fails when another slot becomes the query.

**Decision.** Treat all four held-out positions as required for this generator.
Use shared `--require-rotations-identifiable`, the larger `--rotate-query` census,
and an exhaustive cyclic-start probe.

**Alternatives rejected.** Declaring the production query slot fixed would be
cheaper but less reusable for shuffled training pipelines. Individual witness
frequency does not prove every complete lesson refutes every rival.

**Probe and limits.** Final counts are 0/48 smoke ambiguities, 0/1,200 census
ambiguities, and 0/768 exhaustive-probe failures. This policy is task-local; an
explicitly ordered curriculum could reasonably choose a diagnostic-only policy.
