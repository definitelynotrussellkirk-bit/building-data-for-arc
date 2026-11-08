# Proposed parametric extension for `44690b1b635f`

This directory is a **prototype**, not a selected production rule. The canonical
setting and canonical generator remain unchanged.

## Parameters

| Parameter | Allowed values | Default | Meaning |
| --- | --- | --- | --- |
| `neighbor_mode` | `cardinal`, `king` | `cardinal` | BFS uses four orthogonal neighbors or all eight neighbors. |
| `phase` | `0`, `1` | `0` | `0` assigns the singleton color to even distances; `1` swaps the parity colors. |

The original setting is exactly `neighbor_mode=cardinal, phase=0`; its
whitespace-normalized Racket hash is the pinned canonical `72a0e00e932b`.
Each episode chooses one setting once and uses it for every demonstration and
query. Inputs retain the canonical marker and wall grammar. The setting is not
encoded in the public challenge; demonstrations must identify it.

## Generate two retained episodes

From the repository root:

```bash
PYTHONPATH=. python generators/44690b1b635f/workspace/parametric/prototype.py \
  --out generators/44690b1b635f/workspace/parametric/evidence \
  --seed 20261023 --demos 3 --queries 4 --difficulty medium
```

The command writes:

- `evidence/public/maze-*.json`: visible demonstrations and four query inputs;
  no setting, Racket source, or query answers.
- `evidence/private/setting-*.json`: source hash, fixed setting, all labels,
  rival evidence, exact Racket text and hashes.
- `evidence/private/manifest.json`: hashes and public/private mapping.

The retained default and `king+phase1` episodes each distinguish all three
other bounded settings in their demonstrations. Every retained query differs
from at least one rival setting, all four query inputs are distinct, and all
Python labels were checked by the local test suite.

## Verification boundary

This recovery environment did not contain the packet's pinned Racket runtime,
so the four materialized programs have **not** been executed here. The default
program is text-identical under the repository normalization used to produce
`72a0e00e932b`; alternate programs remain proposed until replayed through the
full packet. Use the top-level `tools/replay_in_full_packet.py` to restore this
overlay to the immutable packet, then run the official task checks and a
Racket-backed writer regression before acceptance.
