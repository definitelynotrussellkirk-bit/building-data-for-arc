# Contact-mode parametric prototype

This proposed episode family keeps the canonical object segmentation and degree
recoloring, but fixes one private setting for the entire episode:

- `cardinal` — objects touch across a side; this is the exact canonical rule.
- `eight_neighbor` — objects also touch across a corner.

Inputs are matched across settings for a given seed. Every demonstration
contains a corner-only contact and therefore rejects the other declared mode.
The six teaching profiles cover a diagonal pair, bridge, degree-4 fan, mixed
path, boundary contact, and two separated motifs. Four fixed query streams are
independent of the requested query count; the first is a substantive 30×30
canvas.

Generate a private episode:

```bash
python generators/7f2dafa2bee4/workspace/parametric/prototype.py \
  --seed 17 --contact-mode eight_neighbor --demos 3 --queries 4 \
  --out /tmp/contact-mode-private.json
```

Project one public turn without settings, program, or query answer:

```bash
python generators/7f2dafa2bee4/workspace/parametric/prototype.py \
  --seed 17 --contact-mode eight_neighbor --demos 3 --queries 4 \
  --public-query 0 --out /tmp/contact-mode-public.json
```

`prototype.public_id(episode, query_index)` returns the SHA-256 of exactly the
visible canonical turn bytes; private settings, rule source, and query answers do
not enter the identifier.

The adapter and `promotion.json` are authoring inputs only. Qualification must
independently execute both Racket programs and fit settings from demonstrations.
