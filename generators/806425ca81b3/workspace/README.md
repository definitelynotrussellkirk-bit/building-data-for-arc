# Workspace

The selected implementation is `../generator.py`. Workspace tools and prototypes
are never automatically selected as the production generator.

## Portable contract probe

From the outer review packet directory, run:

```bash
python3 review.py run python3 generators/806425ca81b3/workspace/probe_contracts.py --label current --out ../checks/current-contracts.json
```

Use `--compare ../checks/canonical-review/before.json` when that retained baseline
receipt is available. `--root /absolute/path/to/repo` selects a fresh checkout
explicitly. The probe checks exact overrides, invalid controls, schedule label
replay, malformed grids and deterministic valid draws. It discovers the selected
generator through the public reviewer support API. Its lesson diagnostics use
the Python mirror and must not be described as Racket or production evidence.

## Proposed rule family

`parametric/README.md` documents the runnable two-parameter prototype, its real
Racket verifier, public export format and tests. It is deliberately separate
from the selected canonical generator. All four settings change a common lawful
input differently; each retained episode uses one fixed setting.

The small regression witnesses are in
`../counterexamples/review-3fce6bff913adf98.json`. Full source-bound review evidence
is transported in the return's `checks/` files and evidence bundle.
