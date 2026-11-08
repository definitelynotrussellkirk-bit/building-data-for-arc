# Native parametric contact-degree family

`finish=degree_palette` is the exact canonical Racket program. It recolors every
object by the degree of its one-step orthogonal contact-halo graph.
`highlight_max_degree` computes the same graph, derives its maximum degree, and
recolors exactly that complete degree class to 9 while preserving all other
source objects.

The sampler is setting-independent. Its first two demonstrations separate graph
degree from object size, source order, source color, canvas center, and a
Manhattan-distance-one graph. Every episode has four private queries; the fourth
is a 30×30 nine-object case with 20 foreground cells, all four boundary contacts,
and degree classes 0, 1, 2, and 4.

Causal chain: **A** builds the contact graph and computes every object degree;
the **intermediate** is the degree vector and its maximum; **B** highlights the
objects in that maximum-degree class. `rules/wrong_largest_object.rkt` replaces
the degree vector with object sizes and is retained only as a protected-Racket
counterfactual.

Run the bounded authoring audit with:

```bash
python3 audit.py --out evidence/current/authoring-audit.json
```
