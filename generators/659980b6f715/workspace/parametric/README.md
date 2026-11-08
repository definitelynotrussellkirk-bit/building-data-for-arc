# Native `alignment_anchor` family for `659980b6f715`

This directory contains the task-local native adapter proposed for owner
qualification. It does not change `generator.py`, the selected canonical rule,
or training admission.

## Episode parameter

`alignment_anchor` is fixed for the complete episode:

- `top_left` is the default and returns the exact canonical Racket program
  bytes. Each color component is normalized to its own bounding box and both
  normalized shapes are overlaid at the common output's top-left corner.
- `bottom_right` performs the same normalization and overlay, but first derives
  each component's bounding-box height and width and translates each shape to
  the common output's bottom-right corner.

The sampler is independent of the selected setting. It supports 2–6
Demonstrations and 1–4 prefix-stable queries, with four distinct stored queries.
The fourth query is a substantive 30×30 boundary-contact scene. The minimum
two-example lesson rejects the opposite setting and the declared corner,
center, mixed-color and size-role anchor shortcuts.

`prototype.py` is the source model, `adapter.py` is the native controller entry
point, and `promotion.json` is the bounded contract. `alignment_anchor.py` is a
compatibility wrapper for the earlier retained authoring evidence.

## Public projection

`public_view(episode, query_index)` publishes all demonstrations and exactly one
query input. It omits the setting, seed, programs, query answers, future queries,
and the total query count. Public IDs hash only the canonical public bytes.

## Reproduction

From the packet root:

```sh
python3 review.py run python3 -m pytest -q \
  generators/659980b6f715/tests/test_parametric_native.py \
  generators/659980b6f715/tests/test_parametric_alignment.py

python3 review.py run python3 \
  generators/659980b6f715/workspace/parametric/audit.py \
  --out generators/659980b6f715/workspace/parametric/evidence/current/self_audit.json \
  --seeds 0 17 31

python3 review.py run python3 -m arcpuzzles parametric qualify 659980b6f715 \
  --out ../checks/659980b6f715/qualification --summary
```

## Evidence boundary

The self-audit is finite: it covers authored seeds and demo/query boundaries and
eight executable candidate policies. Protected Racket checks selected small and
30×30 cases. The inventory, qualification and causal witness bind the exact
returned source, but owner integration, fresh acceptance and training admission
remain separate decisions.
