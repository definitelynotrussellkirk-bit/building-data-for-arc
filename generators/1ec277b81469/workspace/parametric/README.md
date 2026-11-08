# Parametric family: 1ec277b81469

- `finish=canonical` is the exact selected ARC program: independently right-pack
  every row while preserving its nonzero order.
- `finish=fill_largest_bbox` first performs that right-packing, then discovers
  the unique largest same-color 4-connected component in the packed
  intermediate and fills its input-dependent bounding box with color 9.

The sampler authors the target only in the packed state; every source component
is strictly smaller.  The two promised demonstrations use complementary decoy
profiles:

- a modal checkerboard defeats frequency and 8-connectivity shortcuts, while a
  remote target-color singleton defeats whole-color bounding boxes;
- a smaller L-shaped component has a strictly taller, wider, and larger-area
  box than the true size-selected component, defeating bbox-rank shortcuts.

Inputs are shared across settings, counts are independent, and the four-query
bank spans 7x11 through a dense 30x30 protected-Racket stress case.

Useful authoring commands:

```sh
python3 generators/1ec277b81469/workspace/parametric/semantic_sweep.py \
  --seeds 200 --out /tmp/1ec277b81469-semantic-sweep.json
python3 generators/1ec277b81469/workspace/parametric/adversarial_probe.py \
  --out /tmp/1ec277b81469-racket-adversarial.json
```

The first is a fast Python-mirror stochastic teaching check.  The second must be
run through the packet's protected-Racket launcher and remains the executable
label/shortcut evidence.
