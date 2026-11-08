# Workspace

`curriculum_probe.py` audits the selected canonical generator. It enumerates
bounded consecutive schedule starts, compares the rule helper to an independent
Python oracle, checks witnesses and rivals, and holds each member of a five-pair
window out in turn. An independent implementation of the retained
`preserve_first_conflict_only` audit rival remains active even if a future
source accidentally removes that declaration.

Each window also creates four queries distinct from one another and from its
four demonstrations. Every query is assessed using only those demonstrations.
The report includes the complete schedule period, executed generator source
path/hash, probe hash, sampler description, unique-input counts, conflict-count
histogram, and separate ordered, rotated, and four-query results. The public
portable loader compiles exactly the hashed source bytes; the report retains
that hash if the live file changes after import. In a staged snapshot, task-local
bootstraps prefer execution-layout dependencies over repository mirrors, matching
the public loader's manifest selection without weakening its source-tree guard.

From the repository root:

```sh
python3 generators/576426a573af/workspace/curriculum_probe.py \
  --seed 17 --starts 64 --bands none,easy,medium,hard \
  --out ../checks/repair/curriculum-portable-final.json
```

The final version-2.2.0 report covers 256 ordered windows, 1,280 rotations, and
1,024 four-query checks with no failures. Its 284 band/index draws represent
233 unique grids; canonical anchors can repeat across difficulty bands, while
each lesson's inputs remain distinct. The prior baseline and intermediate
version-2.1.0 reports remain separate evidence. These are bounded direct-sampler
results using Python labels; the production command and Racket receipts provide
reference-executed labels separately.

`parametric/` contains a separately proposed family extension. Workspace code
is never selected automatically; the canonical implementation is `../generator.py`.
