# `e8504fcc371b` native parametric family

`trail_mode=straight_to_border` preserves the catalog program byte for byte.
`trail_mode=border_hook` adds a sequential second step: trace the commanded ray
to obtain its border endpoint and length, then continue clockwise around the
perimeter for exactly that many positions.  The hidden setting never affects
input sampling.

The input domain is intentionally narrow: exactly one command marker and one
seed marker.  That restriction preserves the semantics of the canonical source,
which selects the last command and last non-command nonzero cell.  Spatial
coverage comes from the output trajectory rather than unrelated input noise.

Run focused tests through the packet wrapper:

```bash
python3 review.py run python3 -m pytest generators/e8504fcc371b/tests -q
```
