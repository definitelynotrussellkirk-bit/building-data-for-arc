# Parametric mirror-axis prototype

This is a **task-local curriculum prototype**, not a change to the selected
canonical task.  The production/default rule remains `mirror_axis=vertical`.
The alternate `horizontal` setting keeps the same input palette, output roles,
cellwise classification, and paired-versus-solo reasoning; only the mirror
coordinate changes.

`prototype.py` chooses `mirror_axis` once from the episode seed, searches the
selected generator for four inputs on which the two settings disagree, labels
three demonstrations and one query with the complete selected Racket program,
and verifies both Racket programs against an independent Python mirror.  The
public JSON omits the query answer.  The retained evidence JSON includes the
query answer, rival answer, exact source hashes, accepted sample indices, and
Racket/Python parity result.

Run from the packet root so the pinned Racket runtime is selected:

```sh
python3 review.py run python3 generators/b9b63ae52d91/workspace/parametric/prototype.py \
  --seed 20261020 \
  --out-public generators/b9b63ae52d91/workspace/parametric/examples/seed-20261020-public.json \
  --out-evidence ../checks/parametric/seed-20261020-evidence.json
```

The parameter is intentionally small and lossless.  A lesson is rejected unless
at least one demonstration refutes the other axis and the held-out query also
has different answers under the two exact programs.  This checks the actual
teaching episode rather than merely showing that the two rules can differ in
principle.

## Current native family (supersedes the one-query authoring prototype)

`adapter.py` is the native entrypoint. `promotion.json` declares `mode` as
`vertical`, `horizontal`, or `paired_rows`, with 2–6 demonstrations and 1–4
prefix-stable queries. Store all four queries; use the packet's existing
`preview-public export` to shuffle the complete bank and reveal one at a time.
The default reads `rules/canonical.rkt`, copied byte-for-byte from the selected
catalog authority. The production generator and authority remain unchanged.

`paired_rows`: first perform the vertical red/gray classification. Find the
largest red 4-connected component, breaking equal sizes by row-major discovery;
then turn gray cells in that component's rows yellow (4). Red, background, and
other gray cells remain unchanged. No red component means no relay. Odd-axis
cyan cells are red under the original rule. `wrong_intermediate.rkt` selects
rows from original cyan components instead, while preserving the final stage.
That changes the answer on the retained qualified counterfactual.

Inputs are identical across settings. Independent hashed RNG streams produce
queries at 9×12, 15×11, 22×25, and 30×30; the last has hundreds of cyan cells,
contacts all edges, and contains distributed paired and asymmetric cells.
Two teaching examples are selected from a bounded 48-scene bank against 24
explicit Python policies. The bank contains a constructive dense-six-cell vs
larger-box-five-cell-L witness; this repairs the measured area shortcut without
increasing the two-demo minimum. Selection is conditioned on rival differences
on the independent four-query bank, not on the chosen setting. Actual survivors
are computed from demonstrations alone. Requests fail closed if the finite
cover cannot be found; the 32-seed audit measured no such failures. This is not
universal identification or a proof for all seeds.

Run from the packet outer directory:

```sh
python3 review.py run python3 generators/b9b63ae52d91/workspace/parametric/audit.py --out ../checks/b9b63ae52d91/audit-new.json
python3 review.py task-tests b9b63ae52d91 --phase after --out ../checks/b9b63ae52d91/tests-new
python3 review.py run python3 -m arcpuzzles parametric qualify b9b63ae52d91 --out ../checks/b9b63ae52d91/qualification-new --summary
```

The audit records 480 episodes, 3,840 labeled-pair checks (not unique grids),
314 unique inputs, 24 policies, and 49 independent protected-Racket evaluations.
The bounding-box regression includes Racket labels for both fitting old demos,
a separating query, and the repaired demos. Most census labels remain Python
claims; native qualification executes every retained setting/job pair.

The legacy `prototype.py` report now serializes only strict train/test fields
for its public section. Its previous selected-axis leak has a regression;
the retained public example is sanitized and copied under its exact-byte hash.
The sanitized `seed-20261020-public.json` remains an authoring-only compatibility
alias because the delta-return format disallows deletion; never use that legacy
filename as a model-facing export.
Native exports use the existing verified sequential preview, not that historical
one-query authoring CLI. Settings, construction indices, programs and answers
are private. No owner acceptance or training admission is claimed.
