# `copy_limit` parametric prototype

This task-local **proposed prototype** varies one episode-level rule parameter while retaining the original object roles and geometry:

- `copy_limit=to_edge` — canonical/default behavior. Each blue edge marker selects the uniquely overlapping hollow 4×4 frame and repeats it in 4-cell steps to the marked edge, clipping the last copy.
- `copy_limit=one_copy` — nearby alternative. Selection, direction, color, and translation size are unchanged, but each marker emits only the first translated frame.

The value is chosen exactly once from the episode seed and held fixed across three demonstrations and one query. Retained inputs have at least one additional legal copy beyond the first, so the two settings differ. Labels and counterfactual labels are produced by live Racket execution; the independent Python probe is only a cross-check. Public files omit the parameter, Racket code, and query answer.

From the packet extraction root:

```bash
python3 review.py run python3 \
  generators/f4d4fb4404c6/workspace/parametric/prototype.py \
  materialize --seed 20 --out ../checks/parametric/copy-limit-v1

python3 review.py run python3 \
  generators/f4d4fb4404c6/workspace/parametric/prototype.py \
  verify --out ../checks/parametric/copy-limit-v1
```

The materialization output directory must not already exist. The evidence includes exact per-setting Racket programs, hashes, two complete private episodes, redacted public challenges, a setting-difference witness, all query rotations, canonical-default parity, a file manifest, and replay verification.

This prototype does not change the selected canonical authority, add a production parametric API, or grant approval to the alternative setting.
