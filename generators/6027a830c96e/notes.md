# Working notes: 6027a830c96e

## Final repair state — review-b74b5b5c70306a18

Final generator SHA-256:
`ebdc95cab58d27d0b8b1ca01b86b5bbc1fba055bbffc23cbf9fbebc5e971ca4a`.
Canonical rule hash: `ca56dbdca539`; authority unchanged.

The v4.0.0 rewrite resolves prior audit findings A2/A3:

- validation now distinguishes a visual rectangular panel from the exact
  connected perimeter object required by the Racket rule;
- selected-frame own-color contamination is rejected by the retained
  `counterexamples/own_border_color_merges_frame.json` regression;
- a canonical impure **nonselected** distractor remains accepted, because the
  selected frame and row-major external selector still satisfy authority;
- the only declared controls are exact and observable: `grid_h`, `grid_w`,
  `n_frames`, and `selector`.

The five-profile schedule stays at canonical scales and varies selected position,
panel count, selector, palette, and interior. Semantic rivals cover leftmost,
rightmost, largest, and tight-crop shortcuts. `tests/test_generator_contract.py`
has 69 passing regressions. Exact period enumeration passes 15 lessons/75
rotations; the broader census passes 300 lessons/1,500 rotations with no
ambiguity or errors.

The full battery is 11/12 only because the shared semantic gate reports
`declared_period_not_enumerated` without a way to consume the source-bound
census it requests. All eleven other stages pass, and the substantive semantic
checks inside that stage pass. Keep `LESSON_SCHEDULE_PERIOD = 5`; deleting honest
schedule metadata merely to suppress this shared-tool warning is not an
acceptable task-local repair.

Known scope limits: overlapping panels, multiple external selectors, or multiple
panels sharing the selector color are outside the intended manifold and are
rejected. No shared helpers, canonical rows, or Racket authority were changed.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-82548b4b24894693:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `afcd9f3b168762d71825a4f83c776dda3815c970af6c93fa117d8cf21d6cf710`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolved against accepted exact-source repair review-b74b5b5c70306a18:v0001 under reviewer-reported policy. Both named findings addressed: selected-frame connected-component contamination is rejected with the retained minimal counterexample; exact observable grid/selector controls replace ignored axes.69 reported task tests and override/authority checks; fixed-seed and broader reported lesson evidence retain their finite scopes. Canonical authority unchanged; original finding/assessment retained. No claim of universal coverage or training admission.

### Assessment or prior finding

## 6027a830c96e

Generator SHA256: `afcd9f3b168762d71825a4f83c776dda3815c970af6c93fa117d8cf21d6cf710`.
Rule SHA256: `294d052e6add463e9a0c76fb4f37cc136283cbd3bf9d00deedbfe0b535c51c30`.
Evidence: `checks/audits/6027a830c96e.json`.

**A2 — Reproduced validator false negative causing reference execution failure.**

Generate seed 0, sample 0, easy difficulty, no overrides. Change the selected frame's interior cell (row 6, column 1) from 0 to 1, its border color. The complete original and mutated grids are retained, so coordinate conventions are unambiguous. The geometric validator returns an empty error list, but the actual Racket rule fails with `hash-ref: contract violation`, expecting a hash and receiving #f while reading bbox. A geometric border-crop rival produces an output, also retained.

The unchanged rule selects frames through connected-color objects and a perimeter-size condition. Joining interior color to the frame violates that object condition. The actual sampler excludes frame colors from interior contents, so this witness is **outside documented generator support**. It is a validator/reference mismatch, not a demonstrated spontaneous crash from default generation. Suggested repair, not applied: reject same-color content that contaminates a frame component or otherwise validate the exact reference preconditions.

**A3 — Reproduced silently ignored override controls.**

Call `generate(0, 0, difficulty="hard", grid_h=11, grid_w=13, selector=9)`. The observed grid is 19x16 and the singleton selector is color 1 at (13,15). It is byte-for-byte equal as a grid to the unoverridden draw. The target validator accepts it and actual Racket executes. This is a controls/provenance defect on generated output, not a competing output-rule mismatch. The record explicitly uses null for the inapplicable rival output rather than inventing one.

**Additional check:** bands None/easy/medium/hard, seeds 0..2, indices 0..1 produce 24 default draws / 18 unique inputs with no measured validator or Racket execution errors. This small census does not establish general label correctness or rule identifiability. No repairs were made to this target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-82548b4b24894693-v0001/audit_assets.json), manifest SHA-256 `4e6c0c404ecac46bf0025be1e9cac867b8d50bfdc0ff16baef69a23987207892`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `ebdc95cab58d27d0b8b1ca01b86b5bbc1fba055bbffc23cbf9fbebc5e971ca4a`.

# Decisions for `6027a830c96e`

## Inputs and root-cause evidence

The selected baseline was generator SHA-256
`afcd9f3b168762d71825a4f83c776dda3815c970af6c93fa117d8cf21d6cf710`,
with canonical rule hash `ca56dbdca539`. The prior source-bound audit supplied
two concrete leads:

1. A selected frame contaminated by its own border color passed the geometric
   validator but ceased to be a qualifying connected perimeter object, causing
   the Racket rule to fail.
2. Supposed exact controls were silently ignored.

The baseline battery confirmed that these were structural, not isolated:
lint and defect-lint found missing rule pin/strict scalar handling and dead
controls, while override checking accumulated more than forty thousand findings
before timeout. Authority checks were already green, so the rule itself was not
the repair target.

## Rule model chosen

I modeled two related but distinct concepts:

- A **visual panel** is a rectangular box whose perimeter cells all have one
  color. Its interior may contain arbitrary colors, including the perimeter
  color.
- An **exact frame object** is the connected component required by the Racket
  rule: the component is exactly that perimeter and has no connected same-color
  interior contamination.

The external selector is the first row-major nonzero cell outside exact frame
boxes. Its color must identify one visual panel, and that selected panel must be
an exact frame object. Nonselected visual distractors may be impure.

This distinction was forced by canonical data. My first regression assumption
required every panel to be exact; it rejected a canonical training example with
an impure nonselected distractor. I revised the contract rather than weakening
canonical acceptance. The retained mutation changes the **selected** interior to
its border color and remains rejected, preserving the original defect witness.

## Control surface

I removed the broad aspirational axis set and exposed only four controls that
can be recovered exactly from every returned grid:

- `grid_h`: 10 through 12
- `grid_w`: 14 through 17
- `n_frames`: 2 or 3
- `selector`: ARC colors 1 through 9

`observe_overrides` reconstructs all four. Each override is type-strict; `bool`
is not accepted as an integer. Unknown keys and invalid difficulty tokens are
errors. I chose an intentionally small honest domain over a larger partially
implemented API. The override gate passing on the final source is the external
check of this decision.

Rejected alternative: retain legacy names as aliases. That would preserve an
interface whose promised meanings were not realizable and would multiply the
override matrix without adding training value.

## Construction and distribution

Panels are built constructively in separated horizontal slots, keeping a blank
interior margin and a unique external selector. The selected panel is smaller
than at least one distractor, and schedule profiles place it on the left,
middle, and right. This directly defeats “largest panel” and positional
shortcuts while retaining the canonical visual grammar.

The five profiles reproduce the canonical scale/palette envelope:

1. 10×14, palette 6, selected middle
2. 11×15, palette 6, selected left
3. 10×17, palette 7, selected right
4. 12×15, palette 5, selected right
5. 12×17, palette 7, selected middle

The schedule period is declared as five. I kept that honest declaration even
though the current semantic smoke warns unconditionally whenever a period is
declared. Removing it would make the battery cosmetically green while hiding
the exact obligation that the separate census proves.

Rejected alternative: unconstrained random dimensions and panel packing. It
would expand the override/collision surface, drift from canonical morphology,
and make failures hard to attribute without teaching a new semantic distinction.

## Semantic contract

The final generator declares:

- `strict_canonical_like` and canonical acceptance,
- `rule_mirror`,
- witnesses for full interior extent and selected panel not being largest,
  leftmost, or rightmost,
- rivals `tight_crop_selected`, `always_largest`, `always_leftmost`, and
  `always_rightmost`,
- `lesson_identifiable` over every demo/query ordering.

The fixed-period census covers all five starts in easy, medium, and hard at seed
0: 15 lessons and 75 held-out query rotations. A broader census covers 100
lessons per band and every query rotation: 300 lessons and 1,500 rotations. Both
have zero ambiguity and zero materialization/hook/scoring errors.

## Tests and probes retained

`tests/test_generator_contract.py` contains 69 tests covering rule pin/version,
strict call validation, every exact override boundary, canonical acceptance,
Racket-faithful selected-frame contamination rejection, the five profiles,
semantic witnesses/rivals, and every cyclic schedule/query rotation.

`counterexamples/own_border_color_merges_frame.json` is a minimal permanent
regression derived from the prior audit. The blind pre-repair solve and the
post-repair solve are retained separately with honest exposure declarations.

## Failure modes and stopping decision

Potential failures still outside the claimed domain include overlapping frames,
multiple external selectors, and multiple frames sharing the selector color.
They are rejected rather than guessed. The schedule is finite and canonical-
scale; the censuses establish the tested seeds/starts, not universal all-seed
proof.

I stopped because the final source passes all task-local and authority-sensitive
checks, the exact and broad lesson censuses are clean, and the only non-green
battery status is a shared gate that cannot ingest its own requested receipt.
No further task-local change can resolve that without deleting truthful schedule
metadata or modifying shared tooling outside the assignment scope.
