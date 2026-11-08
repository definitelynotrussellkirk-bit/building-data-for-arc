# Parametric prototype: target rank

This bounded prototype varies one meaningful rule parameter: which sorted
monochrome object is recolored. `target_rank=2` is the production/canonical
rule; `target_rank=1` is the nearest nontrivial control. The parameter is
selected once per episode and is not exposed in the public challenge JSON.

Run:

```bash
PYTHONPATH=/path/to/repo python prototype.py --output evidence
```

The materializer emits two complete private episodes, two public challenges,
the exact generated Racket programs, and a hash receipt. It uses an independent
same-color component oracle and checks rank 2 against the production mirror.
When a packet Racket executable/bridge is available, replay the two `rule-*.rkt`
files there; this reconstructed runtime did not retain the packet's oversized
vendored Racket archive after the container reset.
