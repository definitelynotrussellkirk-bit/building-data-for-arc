# Authoring workspace

- `review_plan.md`: original plan and subsequent scope/implementation decisions.
- `reproduce_teaching_gap.py`: source-bound replay of seed 0, medium, indices 5–8. Run through the packet's `review.py run`; optionally pass `--source` for a retained generator snapshot. Exit 1 reports the specific singleton-only teaching failure; labels here are Python mirror observations.
- `parametric/`: runnable proposed min/max-frequency rule extension, public-only episode interface, actual Racket labels and usage.
- `evidence_archive.py`: standard-library pack/verify/restore utility for large exact review evidence, compatible with the existing retention manifest schema.

From `WORK/`, after applying the source patch and extracting the official evidence bundle:

```bash
python3 repo/generators/7944933e200f/workspace/evidence_archive.py verify \
  --work . --manifest checks/compressed/MANIFEST.json
python3 repo/generators/7944933e200f/workspace/evidence_archive.py restore \
  --work . --manifest checks/compressed/MANIFEST.json \
  --destination /absolute/new-restored-work
```

The compression manifest records every original path, size and SHA256. Existing different content is not overwritten. Restored large censuses are exact retained records, including intermediate runs; they are not all final-source evidence. The final generator is version 3.1.1, SHA256 `a0ccc92d7b4cb372cbd538f12851b45efdb78245fb5666af31965714424ad7cd`. See `REVIEW.md` for which receipts support the final result.
