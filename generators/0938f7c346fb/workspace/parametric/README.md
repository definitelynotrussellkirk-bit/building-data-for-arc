# Query operand order family for 0938f7c346fb

The canonical program first infers the unique operation demonstrated by panels
`A`, `B`, and `RESULT`, then applies it to query panels `X` and `Y`.

This native family varies one episode-fixed parameter:

- `xy` (default): apply the inferred operation to `X, Y`; this is the exact
  canonical Racket source, byte for byte.
- `yx`: apply the same inferred operation to `Y, X`.

Both programs infer the same operation and execute on the same input grammar.
The parameter becomes visible on directional `left-minus` examples; every
lesson starts with such a demonstration, followed by other operation families.
Inputs are matched across settings for a fixed seed. Episodes support 2–6
demonstrations and exactly four distinct queries; the fourth query is a
substantive 30×29 input (five width-5 panels plus separators).

`adapter.py` exposes the native `program(settings)` and
`generate(seed, settings, demos, queries)` interface. Protected-Racket native
qualification is the label authority; Python mirrors are deterministic sampler
checks rather than independent acceptance.

## Reproducing the bounded audit

From the repository root:

```bash
PYTHONPATH=src:shared/runtime python3 \
  generators/0938f7c346fb/workspace/parametric/self_audit.py \
  --seed 0 --seed 17 --demos 2 --demos 3 --demos 6 --queries 4
```

The audit enumerates a finite shortcut family and reports the first
demonstration that rejects each rival. It does not claim universal rule
uniqueness. Native qualification and the private causal witness remain the
protected-Racket label authority.
