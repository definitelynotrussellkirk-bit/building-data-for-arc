# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Reusable curriculum probe

From the extracted packet root:

```sh
python3 run_with_racket.py python3 generators/31e43af4bcfa/workspace/probe_curriculum.py \
  --seeds 2 --starts 24 --out ../checks/probe-final.json
```

Use a new output path for each run. The probe finds its own library or staged
runtime through public reviewer_support helpers; --root can bind an explicit
tree. It reads canonical labels only for authoring checks. Do not use it during
a visible-only solve.

Every run checks the 1,260 combinations of four difficulty bands, three object
counts, five heights, seven widths, and three profile residues. The command
above also checks 192 ordinary overlapping windows (seeds 0..1, starts 0..23,
four bands) and all 1,152 single-query holdouts. Twenty-four starts cover the
combined period-three profiles and period-eight dimension anchors.

The report includes all rival namespaces, a per-pair canonical-fit matrix,
source and canonical hashes, exact counts and unique-input counts, every
failure, and the first input/output witness for each declared refutation. A
failure exits nonzero. Generated outputs use the Python mirror; these are not
Racket authority labels. The public lesson-census and apply commands provide
separate reference-backed evidence. Finite success never proves universal
identifiability or changes approval status.
