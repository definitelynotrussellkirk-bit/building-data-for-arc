# Working notes: 506e262f9354

## Repair decision

The executable canonical Racket rule is the authority.  It uses the absolute
bottom-row index, not the length of the color-7 line, and it overwrites every
cell outside its triangle with zero.  Earlier prose described Chebyshev rings,
line-length height, and preserved decoys; those descriptions were not faithful
to the selected executable rule.

The sampler now emits a deterministic three-example curriculum: one
canonical-core sample and two teaching samples per period.  Teaching samples
shift the source line down and add an erasable decoy outside the selected
triangle.  Thus every normal three-demonstration window contains evidence
against both strongest canonical-fitting shortcuts.

## Authority synchronization

The canonical `program_solution` text was copied exactly into the active
`racket_target.target_code` fields for both the training and augmented base
records.  Their legacy `raw_code` fields remain unchanged for provenance.  The
old and canonical texts were behaviorally equivalent on the gate, but active
authorities should be exact-text synchronized rather than merely equivalent.

## Review assets

- `workspace/reference_probe.py` is an independent oracle/rival probe.
- `tests/test_generator.py` covers controls, malformed inputs, canonical
  parity, curriculum identifiability, and both counterexamples.
- `counterexamples/review-03a14c3c057deb90-v0001/` retains exact inputs,
  selected outputs, rival outputs, and disagreement coordinates.
- Imported associated notes retain original evidence and timestamps in
  `evidence/associated_notes.jsonl`.

## Full-height exact override correction

The first complete after-battery found that the sampler excluded
`n_sevens == grid_h` on teaching indices even though both axes advertised that
lawful combination.  The initial implementation reserved a shift row by
shrinking the allowed source length, causing 180 undeclared rejections in the
55,800-draw override matrix.  The final implementation reserves a shift row
only for *default* teaching draws.  When an exact override fills the full
height, the source necessarily starts at row zero and the requested outside
triangle decoys remain available; default lesson generation is unchanged.
The regression is
`test_full_height_source_override_is_supported_even_on_teaching_indices`.
## Current reviewer considerations

Source SHA-256: `762a30ac71d7bb9e779a6ce0948247878740259cac499842ef991e2863f20ec5`.

# Decisions for 506e262f9354

## 1. Preserve the canonical executable rule

**Choice.** Treat canonical Racket hash `d19e95f77d58` as the label authority
and change the sampler, documentation, tests, and active duplicate rule text
around it.

**Why.** The canonical outputs and executable program agree.  The defects were
in the generator's stated semantics and lesson distribution, not in the rule.

**Rejected alternative.** Reinterpret the task as line-length height or
Chebyshev-distance rings.  Both would contradict the selected executable rule
on lawful shifted-source inputs.

## 2. Synchronize active rule text, retain archival text

**Choice.** Copy the exact canonical `program_solution` into both active base
`racket_target.target_code` fields.  Leave each legacy `raw_code` unchanged.

**Why.** The pre-repair programs were behaviorally equivalent but exact-text
divergent.  Active authorities should identify one source; archival provenance
should not be rewritten.

**Evidence.** Final `authority_sync` reports
`selected_synchronized_archival_divergent` with execution parity PASS in
`checks/after-final-2/checks/506e262f9354_after_battery_summary.json`.

## 3. Use a period-three curriculum

**Choice.** Every three consecutive default samples contain one canonical-core
input and two teaching inputs.  Core inputs preserve the visible public
profile; teaching inputs shift the source down and place at least one lawful
non-7 decoy outside the selected triangle.

**Why.** Three demonstrations are the declared lesson minimum.  The schedule
therefore gives each production lesson direct evidence against both strongest
canonical-fitting shortcuts without relying on favorable random draws.

**Rejected alternatives.** Pure random mixing could produce all-core lessons.
All-teaching lessons would remove the canonical anchor and reduce profile-floor
support.

## 4. Declare only exact, grid-observable controls

**Choice.** Expose `grid_h`, `grid_w`, `n_sevens`, `column_position`, and
`decoy_count`.  Each can be recovered from the returned grid and is checked in
all bands.

**Why.** The old texture-oriented surface obscured what was actually
controlled.  The replacement axes correspond to independent, visible
properties and make override failures diagnosable.

**Boundary correction.** The first implementation reserved one row on all
teaching indices and accidentally rejected lawful exact combinations where
`n_sevens == grid_h`.  The final implementation reserves that row only for
default teaching draws.  An exact full-height override starts at row zero and
still honors all other controls.  Evidence is the red/green pair
`checks/tdd-override-red/` and `checks/tdd-override-green/` plus the final
55,800-draw override pass.

## 5. Keep two explicit rival programs

**Choice.** Declare and test:

1. `line_length_triangle`: expansion begins at the top of the source line;
2. `preserve_decoys`: nonzero cells outside the triangle survive.

**Why.** Both fit every canonical labeled pair, are simple enough to be
plausible learner shortcuts, and disagree on separately controllable lawful
features.

**Probe.** `workspace/reference_probe.py` implements the authority and rivals
independently of production geometry.  The Racket-backed shifted-source witness
has 16 disagreement cells in `checks/shortcut-witness/verification.json`.

## 6. Scope and limitations

The sampler intentionally restricts inputs to one contiguous vertical color-7
source and at most four outside-triangle decoys from colors
`{1,2,3,4,5,6,9}`.  It does not claim the canonical Racket program is defined
for multiple 7-columns, gapped sources, color 8 in the input, or decoys inside
the output triangle.  `self_check` rejects those cases instead of assigning
unstated semantics.

The lesson results establish finite identifiability against the declared
rivals: 300 production lessons and 1,200 query rotations.  They do not certify
uniqueness against undeclared hypotheses or every possible cyclic start.

## 7. Current proposed expansion-direction family

`expansion_direction=up|down` remains episode-fixed. The exact canonical `up`
source expands upward from the bottom source endpoint; proposed `down` expands
downward from the top endpoint while preserving clipping, triangle growth and
horizontal 7/8 parity. Production generator SHA-256
`762a30ac71d7bb9e779a6ce0948247878740259cac499842ef991e2863f20ec5`, canonical
program SHA-256 `7d00cd1a50d3b572eb7a50d096cb5d01f0e7af4d8f9bc403d42a3b905b20dc6f`
and normalized authority `d19e95f77d58` are unchanged.

The current merge keeps `review-12dd959303a088a8`'s writer: finish the full batch,
reject duplicate visible IDs before any public write, then emit in content-ID
order. It adds an exact payload/ID assertion during the same preflight. Prior
seed-1 saved visible bytes are preserved. No writer replacement or sampler change
is selected from the parallel return.

## 8. Current claims interface and evidence boundary

The useful `review-7ad1eda9e324a011` interface is selected: `generate_claims`
produces deterministic Python labels without constructing a bridge, while the
thin task-local adapter declares `up|down`, default `up`, demonstrations `3..8`
and independent queries `1..8`. Python labels remain claims for independent
Racket replay. Existing Racket paths and caller-owned bridge reuse remain intact.

Current disposition, exact source bindings and focused tests/replay are in
[evidence/conflict-reconciliation.json](evidence/conflict-reconciliation.json).
The prior 76-test writer results and 79-test/formal qualification receipt remain
reviewer-reported evidence for their original bytes; they do not qualify the
merged implementation. Current focused replay does not claim formal qualification,
acceptance, production approval, audit resolution, training admission, universal
identifiability or learning benefit. Variants remain proposed and unaccepted.
