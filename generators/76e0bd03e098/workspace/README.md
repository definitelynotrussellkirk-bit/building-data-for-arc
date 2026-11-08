# Workspace

The selected implementation is `../generator.py`. Workspace code is reviewer
tooling and is never production label authority.

## `reference_probe.py`

Reusable independent probe for task `76e0bd03e098`:

- locates the repository portably with `reviewer_support.find_root`;
- loads all canonical input/output pairs;
- computes first-seen color order, both elbow paths, branch summaries, and an
  independent expected output without importing generator helpers;
- provides the minimal blocked-fallback teaching witness;
- can invoke the packet's real Racket runtime for parity and fails loudly when
  the runtime is unavailable.

Focused use is demonstrated by `../tests/test_generator.py`. Keep new semantic
assertions in this probe independent of production helpers so a shared mistake
cannot make generator and tests agree falsely.

## `topology_probe.py`

A deterministic shortcut-risk diagnostic that separates raw pixel diversity from
translation- and palette-normalized relative topology. Reproduce the retained
900-draw report from `WORK/repo` with:

```bash
python3 generators/76e0bd03e098/workspace/topology_probe.py \
  --draws-per-band 300 --out ../checks/topology-self-review.json
```
