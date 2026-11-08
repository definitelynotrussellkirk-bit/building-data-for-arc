# Native `bridge_axes` family for `7515881f2786`

This directory contains the task-local native adapter proposed for owner
qualification. The production generator remains unchanged, and the approved canonical
authority remains unchanged.

## Episode parameter

`bridge_axes` is fixed for the complete episode:

- `both` is the default and returns the exact canonical Racket program bytes;
  consecutive cyan anchors are bridged horizontally and vertically.
- `horizontal` retains only same-row consecutive-anchor bridges.
- `vertical` retains only same-column consecutive-anchor bridges.

For each selected axis, the rule first groups the input-derived cyan anchors by
row or column and sorts their coordinates. Those ordered consecutive-pair lists
are the intermediate consumed by the painting step, which fills only zero cells
strictly between each pair.

The setting-neutral sampler supports 2–6 demonstrations and 1–4 prefix-stable
queries, with four distinct stored queries. Every scene exposes positive
horizontal and vertical bridges, exact-two lines, and three-anchor chains; the
fourth query is a substantive 30×30 boundary-contact case. Two demonstrations
reject the other settings and the declared none/exact-two/per-line/longest-line
shortcuts.

`prototype.py` is the source model, `adapter.py` is the native controller entry
point, `promotion.json` is the bounded contract, and `audit.py` is the reusable
finite-rival and protected-Racket checker. The older `verify.py` remains usable
for compatibility with retained evidence.

## Public projection

`public_view(episode, query_index)` publishes all demonstrations and exactly one
query input. It omits settings, programs, seeds, answers, future queries, and the
total query count. Public IDs hash only canonical public bytes.

## Reproduction

From the packet root:

```sh
python3 review.py run python3 -m pytest -q \
  generators/7515881f2786/tests/test_parametric_native.py \
  generators/7515881f2786/tests/test_parametric_bridge_axes.py

# Compatibility replay of the retained materialized prototype evidence:
python3 review.py run python3 \
  generators/7515881f2786/workspace/parametric/verify.py \
  --seed 20261021 \
  --out ../checks/7515881f2786/retained-verification.json \
  --artifact-dir ../checks/7515881f2786/retained-materialized

python3 review.py run python3 \
  generators/7515881f2786/workspace/parametric/audit.py \
  --out generators/7515881f2786/workspace/parametric/evidence/current/self_audit.json \
  --seeds 0 17 31

python3 review.py run python3 -m arcpuzzles parametric qualify 7515881f2786 \
  --out ../checks/7515881f2786/qualification --summary
```

## Evidence boundary

The audit is finite: it covers authored seeds and count boundaries and nine
executable candidate policies. Protected Racket checks selected small and
30×30 cases. Source inventory, qualification and the causal witness bind the
returned bytes, while owner acceptance and training admission remain pending.
