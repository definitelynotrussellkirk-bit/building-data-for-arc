# Endpoint-policy parametric family

This proposed family keeps the task's mirror row, 6-bars, input-side marker,
and erase/move behavior fixed. The hidden `destination_endpoint` setting
chooses which endpoint of every bar receives the moved reflected pair:

- `opposite` — the endpoint away from the input 2 marker; this is the exact
  canonical Racket program, byte for byte.
- `adjacent` — the endpoint next to the input 2 marker.

Inputs are sampled without consulting the setting. Every episode has 2–6
training demonstrations and exactly four novel queries. The final query is a
lawful 29×30 balanced scene (odd height is required by the central mirror),
with long bars and boundary contact. Public projection reveals demonstration
inputs/outputs and query inputs only; sequential turn zero is exactly the
single-query public challenge.

The native owner qualification independently executes every returned label in
protected Racket. Run the focused authoring checks from `WORK/` with:

```bash
python3 ../review.py run python3 -m pytest \
  generators/96ebf3053dbe/tests/test_parametric_endpoint_policy.py -q
```
