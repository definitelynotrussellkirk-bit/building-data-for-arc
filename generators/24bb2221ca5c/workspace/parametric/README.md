# Native parametric family — `24bb2221ca5c`

This task-local family preserves the exact canonical default while varying one
fixed episode rule:

- `all` — fill every enclosed region of every component (the canonical source,
  byte-for-byte);
- `largest_hole_area` — fill only the component whose enclosed regions have the
  greatest total area; and
- `most_holes` — fill only the component with the greatest number of enclosed
  regions.

Every generated scene contains a large single-hole component, a two-hole dense
component, a sparse large-bbox ring, and an open side-gap control. The first two
demonstrations identify all three settings while also refuting first-component,
last-component, largest-bbox, smallest-hole-area, and identity shortcuts. Inputs
are independent of the hidden setting and of requested demo/query counts. The
fourth query is a substantive 30×30 border-contact stress case.

## Native API

`adapter.py` exports the required calls:

```python
program({"fill_policy": "largest_hole_area"})
generate(seed=17, settings={"fill_policy": "largest_hole_area"}, demos=3, queries=4)
```

The public solver projection is `prototype.public_turn(episode, query_index)`.
It returns all labeled demonstrations and exactly one query input, with no
setting, program, query label, future query, count, or final-turn hint.

## Verification

From the packet root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/24bb2221ca5c/tests/test_generator_24bb2221ca5c.py \
  generators/24bb2221ca5c/tests/test_parametric_adapter.py

python3 review.py run python3 \
  generators/24bb2221ca5c/workspace/parametric/audit.py \
  --out generators/24bb2221ca5c/workspace/parametric/evidence/current \
  --seed 0 --seed 17 --demos 3 --queries 4
```

The retained audit executes all six setting/seed episodes through protected
Racket, checks all 42 labels, scans five finite rivals from demonstrations alone,
and writes one private wrong-intermediate witness. The current witness is rebound
to the exact native qualification source binding before the final return is
packaged.

## Causal dependency

Step A computes component-local enclosed regions and their input-dependent area
and count. Step B selects a component using those measurements, then fills its
holes. The retained ablation substitutes component bbox area for enclosed-hole
area. It selects a different component and produces a different protected-Racket
output. This is a bounded authored witness, not a universal proof of algorithmic
depth or training benefit.
