# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

`probe_contract.py` is a read-only Python geometry, override, and declared
witness/rival census. It reads integer ranges from `AXES`, checks all compatible
exact tuples in every difficulty band at sample indices 0 and 1, checks total
palette-only adaptation, and reports a small default object-count frequency
census. The current ranges produce 4,704 exact scenes, 40 palette-only scenes,
and 1,200 frequency samples. It executes no Racket and supplies no authoritative
labels; its witness and rival results are Python proxies.

From the review packet's `WORK/` directory:

```bash
.venv-review/bin/python -B repo/generators/457b4958145b/workspace/probe_contract.py --out checks/contract-tool.json
```

The required `--out` path is relative to the caller's working directory. Source
resolution uses `reviewer_support.find_root(__file__)`, so the script also works
from a relocated checkout or staged runtime. The receipt records the exact
command, working directory, source/tool hashes, declared hooks, counts, and
failures. Existing review evidence remains unchanged.
