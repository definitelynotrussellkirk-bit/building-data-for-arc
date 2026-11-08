# Working notes: f112ec4615da

## Current rule and source binding

Split an even input into equal TL, TR, BL, and BR quadrants. At each local
coordinate, return the first nonzero value in priority order **TR > BL > BR >
TL**, or zero if all four cells are zero. The canonical Racket rule was not
changed; `RULE_HASH` remains `8724ec70a45a`.

Current generator version: `4.0.0`  
Current generator SHA-256:
`6c231b14fb87bf876361232ba1952d15e73c992f373a0119f638876e5ed4da13`

## Prior evidence used as a lead

I used retained return `review-1f4b2a09912ae523:v0001` (ZIP SHA-256
`9340df5935e789419fb991825cd574b5bf63d0eb51553fcc8ef79577df318912`)
only as a lead. It identified two current-baseline issues on source
`438a4a576a6a5790a9f92dc00bba8835fe27f264c13cbfcb6a2ad2ad6fd68cc1`:

1. the frozen root fixture uses a non-portable fixed path; and
2. the strongest known canonical-fitting rival is `global_min_else_max`:
   choose the globally smallest nonzero input color when it is present among
   the four aligned cells, otherwise choose the local numeric maximum.

Both were remeasured on this packet before repair. The frozen fixture is
maintainer-owned and remains unchanged.

## Version 4 decisions

- Reject non-integer `seed`, non-integer or negative `sample_index`, invalid
  difficulty values, unknown overrides, and invalid exact dimensions.
- Preserve the existing profile prior, dimensions, density bands, quadrant
  grammar, five outcome witnesses, and canonical rule.
- Relabel the four semantic roles using 21 of the 24 possible color-rank
  assignments. The excluded assignments `(1,0,2,3)`, `(1,0,3,2)`, and
  `(2,0,3,1)` are exactly the assignments that can let the declared numeric
  color rival survive the generated family. Every production draw now refutes
  that rival by construction while colors remain nuisance labels.
- Declare executable strict-domain, branch-witness, rival, and lesson hooks.
  Production lessons require three demonstrations and one query; the hook
  verifies labels and rejects a lesson when the declared rival fits every demo
  but changes the query.

Focused tests are in `tests/test_review_contract.py`. The final strict semantic
run accepted 600/600 draws, found all six witnesses, verified the rival claim on
60/60 checked cases, and found 12/12 sampled lessons plus all 48 query rotations
identifiable. The larger production-shaped census found no ambiguity in 300
three-demo/one-query lessons or 1,200 query rotations, with 1,199 unique inputs.
This is finite evidence against the declared rival, not a proof against every
possible solver hypothesis.

## Parametric prototype

`workspace/parametric/` contains a **proposed, non-production** extension with
one episode-level parameter, `overlay_priority`:

- canonical/default: `tr_bl_br_tl`;
- alternative: `tl_br_bl_tr`.

The object roles and coordinate-wise overlay reasoning stay unchanged. The
parameter is chosen once per episode; each episode contains two demonstrations
and one query, and every retained pair distinguishes the two settings. Exact
Racket programs and public challenge examples are included. Evidence is in
`checks/parametric/overlay-priority-seed19.json`. This does not change or approve
the selected canonical execution path.

## Remaining blockers and limits

- The after battery is 11/12 green. `authority_sync` alone fails because the
  active canonical `program_solution` and selected `target_code` differ in exact
  formatting, although whitespace-normalized text, rule hash, and execution on
  all 7 canonical pairs agree. Repairing that selected base-authority record is
  outside this task-only edit scope.
- The portable aggregate task-test stage stops before pytest because frozen
  `tests/test_generator_f112ec4615da.py` resolves canonical data beneath the
  task directory. The required fixture is intentionally unchanged. The two new
  portable suites pass independently: 7 tests total, including live Racket.
- No claim is made that the finite declared-rival contract proves universal
  induction, that the parametric prototype is production-approved, or that the
  masked post-repair queries were correct; their private labels remain withheld.
