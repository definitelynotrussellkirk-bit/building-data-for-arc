# Workspace

The selected implementation is `../generator.py`. This directory contains task-local review tools and experiments; workspace files are not selected automatically.

## Curriculum analyzer

`analyze_closure_curriculum.py` measures profile balance, strict canonical-like support, input/output diversity, relation-edge counts, semantic-witness firings, named-rival disagreements, and invalid draws.

Run it against a prepared runtime containing the selected generator:

```bash
PYTHONPATH=/path/to/runtime \
python generators/9713c70409d0/workspace/analyze_closure_curriculum.py \
  --samples-per-band 40 \
  --base-seed 120000 \
  --json-out checks/closure-curriculum-analysis.json
```

A nonzero exit means at least one draw raised or failed `self_check`. This analyzer is a cheap structural monitor; the Racket-backed full battery remains authoritative.
