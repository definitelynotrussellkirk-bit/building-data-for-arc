# Boundary-palette prototype

Status: **prototype**, separate from the canonical repair and not approved for production or training admission.

The bounded hidden parameter is `boundary_palette`:

- `ends1_edges4` — canonical/default: color zero-opposing-pair cells 1 and exactly-one-opposing-pair cells 4.
- `ends4_edges1` — proposed variant: swap those two output colors.

The input scene, color-5 source cells, non-5 cells, and color-2 interior class are unchanged. One palette is selected from seed parity and held fixed for the complete episode.

## Independent episode counts

`build_episode(..., demo_count=..., query_count=...)` validates both controls as positive literal integers. The deterministic schedule has ten distinct `(scene_profile, sample_index)` rows, so `demo_count + query_count` must be at most 10. The Python API retains its historical 4-demonstration/1-query defaults; retained follow-up evidence explicitly requests **4 demonstrations and 4 distinct queries** per setting.

All selected rows witness both palette-dependent classes. The matching complete Racket program labels every demonstration and query; Python is only an assertion mirror.

## Public export privacy

Public files are written with `reviewer_support.public_challenge_bytes` and named from `public_challenge_id`:

```text
challenge-<sha256-of-exact-visible-bytes>.json
```

Only demonstration inputs/outputs and query inputs affect the bytes, ID, or filename. Settings, seeds, Racket programs, query answers, and setting-associated ordinals remain private. The complete batch is duplicate-checked and sorted by public ID before any file is written.

The pre-1.1.0 `ends*_public.json` fixtures remain only as historical baseline artifacts. Version 1.1.0 does not emit those setting-named files; current retained outputs are the `challenge-<visible-content-sha256>.json` files.

## Reproduce the retained follow-up

From the outer extraction directory:

```bash
python3 review.py setup
python3 review.py run python3 \
  generators/22d1f016cb3d/workspace/parametric/prototype.py \
  --out ../checks/parametric-boundary-palette-followup/report.json \
  --write-public ../checks/parametric-boundary-palette-followup/public \
  --demo-count 4 \
  --query-count 4

python3 review.py run python3 -m pytest \
  generators/22d1f016cb3d/tests/test_parametric_boundary_palette.py -q
```

Retained complete programs are `racket/ends1_edges4.rkt` and `racket/ends4_edges1.rkt`. The default file is byte-for-byte the canonical ledger source with normalized rule hash `2219db85ca5f`. Evidence is bounded to seeds 18 and 19 and the declared two-value rival; it does not establish production approval or universal identifiability.
