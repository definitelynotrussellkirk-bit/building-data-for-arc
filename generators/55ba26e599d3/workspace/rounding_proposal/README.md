# Proposed canonical Python arithmetic repair

Status: **proposed**, independently of the separate parametric family. The
selected `generator.py`, its existing tests, canonical Racket program, catalogs
and approval records have not been modified by this proposal.

## Defect and exact proposed change

The canonical Racket computes the floating interpolation fraction first, then
multiplies it by the endpoint displacement. The selected Python `_line_cells`
multiplies integers first, then divides. Floating rounding makes these orders
observably different: for endpoints `(0,0)` and `(11,22)`, step 15 evaluates
`(15 / 22) * 11` to `7.499999999999999`, giving canonical row 7, whereas
`15 * 11 / 22` is exactly `7.5`, giving Python row 8 under ties-to-even.

`canonical-arithmetic-order.patch` changes only those two coordinate
expressions to divide before multiplying. It is an exact unified patch against
generator SHA-256
`9d75ef957334cd4da23262a897308df40322f1f0c6672cfe7171308f640c1372`.
Do not replace canonical floating arithmetic with exact-rational interpolation:
the existing Racket execution is the authority.

## Bounded replay

From the outer extraction directory, run:

```sh
WORK/.venv/bin/python review.py run \
  --receipt checks/55ba26e599d3/rounding-proposal/command.json \
  python3 generators/55ba26e599d3/workspace/rounding_proposal/replay.py \
  --out ../checks/55ba26e599d3/rounding-proposal/evidence.json
```

The standalone replay pins generator, authority and canonical-program hashes;
checks that the shipped patch is exactly the proposed source substitution;
loads the proposed module in memory; and executes the unchanged canonical
program through the same protected Racket evaluator used by native
qualification. It asserts the current mismatch and proposed parity for one
12×23 input and its transpose. Both inputs witness zero-to-red and
blue-to-green behavior, and pass current `self_check`.

Actual execution exited 0: both current mismatches reproduced; both in-memory
proposed outputs matched protected Racket. Each mismatch affects two output
cells. Full private inputs, outputs, program and runtime identity are retained
in `checks/55ba26e599d3/rounding-proposal/evidence.json`; the launcher receipt is
beside it. Evidence paths are relative to `WORK/`.

This is a bounded regression, not a universal parity census. The existing
production test oracle repeats the old Python expression, so it would need a
reference-backed regression when the owner integrates the repair.

## Owner approval boundary

The patch remains unapplied so native qualification can bind the currently
approved canonical generator. The owner must separately integrate the proposed
canonical repair, run relevant checks, and approve the resulting exact source.
Changing that source also invalidates any previously qualified or accepted
parametric source binding and requires fresh qualification and acceptance.
This proposal grants no canonical or parametric approval and no training
admission.
