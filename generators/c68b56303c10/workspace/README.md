# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Distribution probe

`probe_distribution.py` uses the local portable `reviewer_support` helpers and
Python's standard library. It loads the current selected generator from this
source tree, samples each difficulty band, and writes a compact source-bound
JSON report. It does not execute the Racket authority: overlap dimensions are
an independent diagnostic computed from visible input coordinates.

From the packet's `WORK/repo` directory:

```bash
python generators/c68b56303c10/workspace/probe_distribution.py \
  --seed 10007 --count 200 --out ../checks/distribution-after.json
```

The seed and count shown are the defaults. `--out` is required and must name a
new file. The script also works from another working directory when invoked
through its absolute path; source/data discovery is relative to the script.

The report binds the selected generator, canonical ledger, selected rule source,
declared rule hash (null when absent), and probe bytes. Per-band evidence includes
exact and envelope input-profile support, canonical output-shape hits, independent
overlap dimension statistics, input uniqueness, cell counts, and replay coordinates
for failures. Only the first input per band and a compact first failure preview
are retained; the report does not store all sampled grids.

Exit 0 means sampling completed without recorded input/draw failures or source
changes. It does not establish authoritative output correctness, sufficient
canonical support, lesson identifiability, or approval. Compare the recorded
metrics and source bindings when evaluating revisions.
