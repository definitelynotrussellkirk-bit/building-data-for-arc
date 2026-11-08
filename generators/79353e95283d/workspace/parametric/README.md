# Native aligned-panel parameters

The native adapter retains the reviewed Boolean prototype and adds `operation=overlap_components`. The canonical `and` setting uses the exact selected Racket bytes. `or` and `xor` reuse the existing prototype programs. The new operation computes aligned overlap seeds and grows them through four-connected foreground on the right panel; output is 2 on reached cells and 0 elsewhere. This is a separately proposed rule extension, with production generator and authority unchanged.

## Implementation plan

1. Add focused tests for literal reachability, canonical bytes, strict requests, matched inputs, independent counts and four novel queries; observe the absent adapter failure.
2. Add `native.py`, thin exact-adjacent-path `adapter.py`, canonical program resource, and `promotion.json`. Keep legacy prototype behavior callable. Generate 2–6 demonstrations and 1–4 independent queries, default 3/4.
3. Construct demonstration motifs containing selected and unselected right components, diagonal-only contacts, multi-hop paths, left-only distractors, and contrasting overlap seeds. Self-audit the declared operations plus a finite family of shortcuts using demonstrations only.
4. Execute labels and boundary stress through protected Racket, inventory final sources, run native qualification, and retain one executed skip-A witness. Package the source/evidence delta for owner acceptance.

## Grammar and teaching limits

Inputs have 1–30 rows and exactly seven columns: two aligned binary three-column panels and a uniform separator color 2–9. Native height extends the canonical sampler’s 1–18 range without changing the canonical program. Exact 30×30 is outside this fixed-width grammar; 30×7 stress must contain active paths, components and distractors throughout its height. No rotation into a horizontal split is promised. Ordinary counts center on three demonstrations; the first two teach the extended rule and the optional third is a canonical-scale anchor.

All settings receive the same inputs for an identical seed/count request. The public projection contains only demonstration input/output pairs and query inputs; settings, reference text and query answers remain private. Four queries are controller data to reveal one at a time. First-query input and demonstration bytes do not depend on how many queries were requested.

Review focus: seedless/distant components; four versus eight connectivity; fill-right versus fill-left; upper/lower size limits; private metadata changing public IDs. Only the finite rivals actually executed are covered; no universal uniqueness or training admission is claimed.

## Run and reproduce

From the outer extracted packet directory (use its dependency-ready Python):

```bash
python3 review.py run python3 generators/79353e95283d/workspace/parametric/audit_native.py --seed 17 --demos 2 --out ../checks/panels-self-review
python3 review.py run python3 -m pytest -q generators/79353e95283d/tests
python3 review.py run python3 -m arcpuzzles parametric qualify 79353e95283d --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/panels-qualification --summary
```

The audit emits four complete four-query episodes (one per setting), protected-Racket teaching/rival evidence, separate public/private JSONL, and exact one-query first-turn projections. Use an unoccupied output path. Once the owner accepts the exact integrated sources, the ordinary native export is:

```bash
python3 review.py run python3 -m arcpuzzles parametric export 79353e95283d --count 4 --seed 23 --demos 3 --queries 4 --out var/datasets/panels
python3 review.py run python3 -m arcpuzzles parametric verify-export var/datasets/panels
```

## Current evidence and repairs

`evidence/final-seed0/` and `evidence/final-seed17/` are the final finite self-reviews: four settings each, two demonstrations and four queries, 26 rivals per setting, 104 protected Racket evaluations per run after cache reuse. The helper derives demo survival before consulting query predictions. `evidence/final-tests.txt` records 129 passing task tests. Queries have heights 1,14,18,30; density varies and the 30-row input carries active connected structure throughout.

Three observed teaching holes were repaired constructively within the minimum two demos: exactly-one-overlap selection, left-panel component growth under AND, and a three-row output cap. A left-only mark now touches an overlap in the small motif; the long motif uses an endpoint and a midpoint seed in the same component. Both singly and multiply seeded selected components remain visible, alongside unseeded components. Original failed lessons and both fitting Racket programs remain in `evidence/alternative-solutions/` for the separate optional alternative-answer stream; they are not ordinary emitted lessons.

The legacy `prototype.py` three-operation/one-query API remains unchanged for compatibility. The native path is `adapter.py`→`native.py`; it exposes all four settings and independent counts. Nondefault lambda programs are wrapped in `rule!` for the native runtime, while the default uses the canonical resource byte for byte. Native qualification is a reviewer result; owner acceptance of exact integrated source remains required.
