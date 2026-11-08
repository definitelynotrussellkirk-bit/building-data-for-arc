# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here. The selected implementation is `../generator.py`; workspace utilities are never selected automatically.

## Mask-space census

`mask_space_census.py` exactly enumerates erasure masks by Latin base, erasure count, completion depth, joint-forcing, and teaching-profile membership. It was added after random probes showed that true three-pass witnesses were not uniformly available across the two Latin classes.

```bash
cd repo/generators/135219aecdb4/workspace
python3 -m pytest -q test_mask_space_census.py
python3 mask_space_census.py --counts 5,6,7 --out mask_space_census.json
```

The retained JSON is the census used for this review. It is evidence/tooling only and does not alter generation.
