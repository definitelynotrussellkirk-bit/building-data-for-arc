# Spout reach: proposed parametric prototype

This task-local prototype extends `bee63e6e52bd` with one private,
episode-fixed rule parameter, `spout_reach`. It does **not** change the
canonical production generator, selected Racket authority, approval record, or
training allocation. The default setting is byte-for-byte canonical.

## Rule parameter

| `spout_reach` | Executed behavior |
|---|---|
| `"full"` | Canonical behavior: continue both diagonal spouts until they leave the canvas. |
| `0` | Preserve the two exterior tip anchors, but add no diagonal cells beyond them. |
| `2` | Paint at most two diagonal cells beyond each exterior tip anchor, clipped by the canvas. |

Distance one is the first cell *after* the preserved outside tip anchor. The
mouth-band fill, actual arm-tip discovery, open-side normalization, shape
color, background-only painting, and yellow output color 4 are invariant. The
canonical source in `canonical-full.rkt` remains exactly 3,173 bytes with
SHA-256 `8a119729a8cfa7e439377928fd01a88ca9dd9ba1d2b570f5a82bba7839c2fe0c`.
Finite settings add a distance guard only at the two diagonal paint sites.

## Current episode contract

The native adapter supports **2–6 demonstrations** and **1–4 queries**
independently. The ordinary/default request is three demonstrations and four
queries. Demo and query streams are sampled separately, so changing the demo
count cannot change any query input and changing the query count only truncates
a stable prefix. All settings receive the same inputs for a given seed/count
request.

The four retained query shapes are 12×18, 18×12, 24×24, and 30×30. Six demo
shapes support the full demo-count range. The separate teaching grammar accepts
exact dimensions 12..30 in both axes, uses every opening orientation, and
constructs four visible post-anchor steps on both rays. Large cases scale the
frame and mouth fill across the canvas instead of padding a small scene.

`first_turn(episode)` returns all demonstrations plus only query 1, without a
total-query count, future query inputs, settings, programs, seeds, or answers.
Its bytes match a one-query request with the same seed and demonstrations.

## Public/private boundary and verification

Public files contain demonstration input/output pairs and query inputs only.
`public_filename()` hashes the **exact canonical public file bytes**, not a
private record or a differently formatted projection. Settings, seeds, Racket
programs, program/source hashes, query answers, runtime identity, and finite
rival outputs remain private.

`write_evidence()` retains one complete Racket-backed episode per requested
setting/seed, all four queries, four size/orientation witnesses, canonical-label
parity, source hashes, and protected-runtime identity. `verify_evidence()`
checks the exact inventory and hashes, current source bindings, exact public
bytes/content IDs, distinct inputs, every selected Racket label, and the
stored demonstration-only finite-rival result. It rejects private-answer or
inventory tampering.

## Native promotion files

- `adapter.py`: exact adjacent-path adapter exporting `program(settings)` and
  `generate(seed, settings, demos, queries)`. Candidate generation is
  subprocess-free: it uses the task-local `predict()` mirror to make claims.
  The native qualification worker independently executes the returned Racket
  program and rejects any claim mismatch, so the mirror is never an authority.
- `promotion.json`: typed settings, canonical default, 2–6 demo bounds, and
  1–4 query bounds.
- `evidence/manifest.json`: source/evidence inventory for owner review. It is
  author-reported inventory, not qualification or acceptance.

## Reproduce from the outer packet directory

```bash
python3 review.py run python3 -m pytest -q \
  generators/bee63e6e52bd/tests

python3 review.py run python3 \
  generators/bee63e6e52bd/workspace/parametric/prototype.py \
  --seed 26023 --per-setting 1 \
  --out generators/bee63e6e52bd/workspace/parametric/evidence/current

python3 review.py run python3 \
  generators/bee63e6e52bd/workspace/parametric/prototype.py \
  --verify \
  --out generators/bee63e6e52bd/workspace/parametric/evidence/current

python3 review.py run python3 -m arcpuzzles parametric manifest bee63e6e52bd \
  --evidence generators/bee63e6e52bd/workspace/parametric/evidence/current \
  --include generators/bee63e6e52bd/tests/test_parametric.py \
  --include generators/bee63e6e52bd/tests/test_parametric_public_names.py \
  --reported-checks 'replace with only checks actually run'
```

Owner qualification, if desired, is a separate explicit step:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify bee63e6e52bd \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/bee63e6e52bd-parametric-qualification
```

Do not run `accept` as part of a rotating review packet. Acceptance re-executes
and records an owner decision; neither this prototype nor its evidence admits
training data.

## Limits

The parameter domain is exactly `{"full", 0, 2}`. Teaching evidence compares
only those three programs, not every imaginable rule. The 12..30 teaching
canvases are a deliberate extension beyond ordinary canonical profiles. The
family remains one frame with one contiguous opening and no obstacles or
interacting pours. Bounded evidence demonstrates current seeds/settings and
source bytes; it does not measure model difficulty, learning benefit, or
universal identifiability.
