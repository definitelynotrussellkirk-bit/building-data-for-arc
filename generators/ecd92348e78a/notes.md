# Working notes: ecd92348e78a

## Current selected account

Version `3.2.1`; canonical rule hash `f25306709cb3`; final generator SHA-256
`7457a230b376ba4c2ba89d83e7378b40745f52dd4ca3dcfd9ff01afd8a6a9fd1`.
For every nonzero color, measure its bounding-box row height, sort colors by
height descending, and draw top-aligned colored bars. Equal heights follow the
selected Racket `grid-colors` order (ascending numeric color), which is now also
used by the Python semantic mirror.

Normal generation remains the v3.2 constructive canonical/separated mixture:
2–5 nonzero colors, distinct measured heights, exact top/bottom witnesses, one
contiguous surviving run per row, and a canonical stacked-block prior. The
repair did not narrow or otherwise change ordinary generated inputs.

## Decisions in this review

- Public calls now validate exact integer seeds/sample indices, supported
  difficulties, known axes, axis value types/domains, and the special
  `n_colors=1`/`single_color` relationship before any draw.
- Joint override conflicts raise `IncompatibleOverrides` with the exact
  `incompatible_axes`; the override checker no longer receives unstructured
  `ValueError` messages.
- `LAWFUL_DEGENERATE_TEXTURES` explicitly declares `tied_heights`,
  `single_color`, and `full_grid`, preserving their rule-valid status without
  hiding them from the defect linter.
- Executable semantic hooks now cover descending order, bbox height rather than
  width, top rather than bottom alignment, and multicolor preservation. The
  teaching contract uses three demonstrations and checks query rotations.
- The canonical ledger text was not edited. Two selected authority
  `racket_target.target_code` copies were synchronized byte-for-byte to the
  canonical `program_solution`; archival `raw_code` and executed semantics were
  preserved.

The historical lead used was associated note `GNOTE-000237`, which documented
an earlier canonical-lambda review and distribution repair. Its claims were
used only as a lead; this review remeasured the pinned baseline and final source.

## Parametric proposal (not selected production behavior)

`workspace/parametric/` contains a runnable two-parameter prototype:
`sort_order ∈ {descending, ascending}` and
`bar_alignment ∈ {top, bottom}`. Parameters are chosen once per episode; the
canonical default is descending/top. Four retained episodes each have three
public demonstrations plus one hidden-query label, and all labels were checked
against the instantiated Racket rule. Every alternative setting differs on all
three demonstrations and on the query. Ascending variants compute canvas height
independently of sort order, fixing the first prototype's truncation bug.

## Evidence and limits

The final twelve-stage battery is all green; portable task tests pass 17/17.
The 300-lesson census retained 1,200 labeled pairs and 1,200 query rotations,
with 1,200 unique inputs and no declared-rival ambiguity or scoring errors.
These are finite checks of the declared domain and rivals, not universal proof.
The three lawful degenerates remain edge-valid but are outside the normal
canonical-like strict profile. The parametric variants are proposals only and
require separate maintainer approval before any production or training use.
## Current reviewer considerations

Source SHA-256: `7457a230b376ba4c2ba89d83e7378b40745f52dd4ca3dcfd9ff01afd8a6a9fd1`.

# Decisions: ecd92348e78a review-f029b9eb30ff87cf

## D1 — Preserve the selected rule and normal distribution

**Original rationale:** associated note `GNOTE-000237` and the current source
indicate that v3.x already repaired the historical axis-honesty and canonical
stacking defects. **Decision:** retain the selected descending bbox-height rule,
canonical stacked prior, separated diversity branch, and normal axis ranges.
**Alternative rejected:** redesigning the input distribution merely to create a
visible diff. The untouched battery already showed strong profile support; the
concrete failures were contracts and authority synchronization, not ordinary
sampling. **Probe:** before/after batteries and the 300-lesson census.

## D2 — Fail closed at the public call boundary

Added exact validation for seed, sample index, difficulty, known axes, axis value
types/domains, and the `single_color` relationship. This prevents typos or
malformed values from silently selecting random defaults. **Alternative
rejected:** rely on `gen_ctx` to coerce or ignore values; the baseline strict
scalar matrix showed that this made advertised controls unverifiable. **Failure
mode:** callers depending on previously ignored bad inputs now receive a clear
`ValueError`, intentionally.

## D3 — Make joint conflicts machine-readable

All relational override failures now use `IncompatibleOverrides` and expose the
exact axis set. **Alternative rejected:** parsing human error strings in the
checker. **Limit:** the conflict list is still task-owned; a future new relation
must be added explicitly and covered by a focused test.

## D4 — Declare lawful degenerates rather than banning them

`tied_heights`, `single_color`, and `full_grid` remain accepted edge-valid modes
because the Racket rule is defined on them. They are now named in
`LAWFUL_DEGENERATE_TEXTURES`, so the linter can distinguish deliberate edge
coverage from an accidental invariant violation. **Alternative rejected:** make
`self_check` reject them solely to silence warnings. They remain outside the
normal strict canonical-like profile.

## D5 — Add executable semantic rivals and match Racket tie order

Added a Python mirror, strict-domain hook, witnesses, and competitors for
ascending sort, bbox width, bottom alignment, and color collapse. `_bbox_stats`
now enumerates colors in ascending numeric order to match selected Racket
`grid-colors` when heights tie. **Alternative rejected:** first-seen order, which
failed the tie-order regression even though ordinary production heights are
distinct. **Limit:** finite declared rivals do not prove unique induction against
all hypotheses.

## D6 — Synchronize selected authority text without rewriting history

The canonical `program_solution` remained the source of truth. Only
`racket_target.target_code` in the selected training and augmented authority
records was replaced with that exact text. `raw_code` was preserved, and the
executed rule hash remains `f25306709cb3`. **Alternative rejected:** editing the
canonical ledger or archived raw source to remove a formatting-only divergence.

## D7 — Use two small, orthogonal prototype parameters

The proposed episode parameters are `sort_order` (descending/ascending) and
`bar_alignment` (top/bottom). They preserve the original objects, bbox-height
measurement, and bar-chart reasoning while changing two inferable behavioral
choices. Parameters are chosen once per episode; descending/top is the canonical
default. **Alternatives rejected:** varying the measured statistic to width
moves farther from the original family; changing palette or grid size is input
variation, not a rule parameter.

The first ascending prototype exposed a dependency: canonical canvas height came
from the first sorted bar. The corrected constructor computes the true maximum
independently of order. Four actual Racket programs were retained with SHA-256:

- descending/top: `beacbe78d9d3c3530931d511c451e6d7a3e9697ec4c9cf19c20d8fff92c1f71f`
- ascending/top: `26fa9a69b303c584941c103ba566f237ff4c78be3cc0b05a6bd1529d0edf226e`
- descending/bottom: `ee4a717110316d26fc6b4a5420fad890c8a6063b47ba15bb088287f3fb1e724a`
- ascending/bottom: `1b4c5e82d77e06d572844ab13c0c900b77f9ea42116f6085e2a7400cd87d5a9f`

Each retained episode has three demonstrations and one query; every alternative
setting differs on all three demonstrations and on the query. **Status:**
proposed prototype only, not selected production behavior.

## D8 — Require both ordered and rotated lesson evidence

The final semantic smoke check retained 12 lessons, 48 labeled pairs, and 48
query rotations with no declared-rival ambiguity. The wider census retained 300
lessons, 1,200 labeled pairs, 1,200 rotations, and 1,200 unique inputs, also with
no ambiguity or scoring errors. **Limit:** random sampling does not exhaust all
seeds or undeclared rivals.

## D9 — Audit conclusions remain separate from the repair

`71fd3c801ee1` is reported clean under 15 portable tests, three canonical pairs,
60 unique generated samples, four rivals, and exact override checks. For
`4bc78768be8b`, the color-2 shortcut is reproduced on 60/60 generated cases but
0/5 canonical cases, with an actual Racket witness. Neither audit target was
edited.

## D10 — Self-review for newly introduced shortcuts

The production generator's ordinary draw path is unchanged; validation and
semantic hooks do not choose colors, dimensions, or placements. The final
300-lesson census has 1,200 unique inputs and all declared rivals are refuted,
so this repair did not introduce an observed constant-label or ordering shortcut.
The only new rule variants live under `workspace/parametric/` and are explicitly
separate from production.
