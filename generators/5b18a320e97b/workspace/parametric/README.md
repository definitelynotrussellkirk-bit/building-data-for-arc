# Native `read_direction` family for `5b18a320e97b`

This task-local adapter keeps the approved production generator unchanged and exposes one episode-fixed rule parameter:

| parameter | values | canonical/default |
|---|---|---|
| `read_direction` | `forward`, `reverse` | `forward` |

`forward` is byte-for-byte the canonical Racket authority. `reverse` changes only the ordered-color binding: after the same object extraction, orientation inference, and spatial sort, it reverses the color sequence before rendering the output stripes. Inputs are setting-neutral, so matched episodes isolate the rule change.

The native contract supports 2–6 demonstrations and 1–4 queries. Demonstration and query streams are independent and prefix-stable. Every maximal episode has four distinct queries sized 12×15, 18×20, 24×27, and 30×30. The first two demonstrations distinguish the selected setting and the retained finite shortcut set.

## Run the focused suite

From the extracted packet directory:

```bash
python3 review.py run python3 -m pytest -q generators/5b18a320e97b/tests
```

## Run the reusable protected-Racket audit

```bash
python3 review.py run python3 generators/5b18a320e97b/workspace/parametric/self_audit.py \
  --out ../checks/5b18a320e97b/self-audit --seed 0 --seed 17
```

## Qualify the native adapter

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify 5b18a320e97b \
  --out ../checks/5b18a320e97b/qualification --summary
```

After qualification, build the source-bound sequential-dependency witness:

```bash
python3 review.py run python3 generators/5b18a320e97b/workspace/parametric/build_causal_witness.py \
  --qualification ../checks/5b18a320e97b/qualification/qualification.json \
  --out ../checks/5b18a320e97b/causal/witness.json
```

The finite self-audit is not a universal identifiability proof, and qualification is not owner acceptance or training admission. Exact-source acceptance remains an owner action.
