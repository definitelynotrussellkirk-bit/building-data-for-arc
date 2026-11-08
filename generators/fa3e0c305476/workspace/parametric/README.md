# Native anchor-hole relay family for `fa3e0c305476`

The default `recolor_scope=all_objects` is the selected canonical Racket rule byte-for-byte: count the non-cyan four-connected regions inside every cyan object's bounding box and map counts `1,2,3,4` to colors `1,2,3,7`.

The alternative `recolor_scope=anchor_hole_matches` adds an input-dependent selector relay. Step A counts the holes of the row-major first cyan object. That intermediate count gates Step B: only objects with the same count are recolored by the canonical mapping; all other cyan objects remain cyan. The first two demonstrations use anchor counts 1 and 3, each with a matching peer and mapped nonmatching objects, so fixed-count, anchor-only, canonical-all, and first-match shortcuts are visibly wrong.

Inputs are matched across settings and support 2–6 demonstrations plus 1–4 prefix-stable queries. They include mapped and fallback counts 0, 5, and 6, compact and enlarged cavities, repeated counts, and a substantive 30×30 six-object query touching all four canvas boundaries. Settings, programs, source indices, future queries, and query labels remain private; `public_turn` reveals one query input only.

`audit.py` checks a finite rival set, public-prefix behavior through the tests, protected-Racket labels, and a wrong-second-anchor counterfactual. Native qualification and exact-source owner acceptance remain separate, and no training admission is claimed.
