# Workspace

The selected implementation is `../generator.py`. Workspace scripts are reviewer
tools and are never selected as the production generator.

## Connectivity and lesson probe

`connectivity_probe.py` checks every rival and witness declared by the current
generator, rather than copying a second name list. It verifies that each declared
canonical shortcut fits all usable canonical pairs, samples every difficulty
band, exhausts all 24 cyclic four-demonstration starts per band, and retains the
exact same-color diagonal-contact witness that distinguishes 4-connectivity from
the plausible 8-connected shortcut.

From the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/0d15074a8931/workspace/connectivity_probe.py \
  --samples-per-band 200 \
  --out ../checks/connectivity-probe.json
```
