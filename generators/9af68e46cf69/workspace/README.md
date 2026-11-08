# Workspace

`probe_contract.py` is a portable, source-bound authoring probe. From the
repository root run:

```bash
python3 generators/9af68e46cf69/workspace/probe_contract.py \
  --per-band 12 --out ../checks/contract-probe.json
```

It loads the selected generator through `reviewer_support`, checks every labeled
canonical pair, samples every difficulty band, and derives witness/rival checks
from the generator's declarations rather than copying their names.

The selected implementation is `../generator.py`. Workspace drafts are never
automatically selected. Minimal semantic reproducers live in
`../counterexamples/` and are covered by `../tests/test_generator_contract.py`.
