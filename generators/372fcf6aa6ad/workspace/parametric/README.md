# Winner-width relay parametric family

This native candidate leaves `generator.py` and the selected canonical Racket
source unchanged.

- `mode=canonical` returns the exact selected source bytes.
- `mode=winner_width_relay` first performs the canonical hole/size/position
  ordering and clockwise rotation. The rotated width of the first-ranked crop
  is then used as a 1-based selector, and that packed crop is recolored to 8.

The authored grammar uses five isolated, distinctly colored objects with hole
profile `[0,0,1,1,2]`. A large zero-hole controller is deliberately larger than
both one-hole frames, so lessons force hole count to precede size and repair the
retained size-first shortcut within this family. The two equal one-hole frames
also exercise the position tie-breaks. The first two demonstrations require
different selectors, so constant-selector rivals are rejected at the supported
minimum of two demonstrations.

The fourth query is a substantive 30x30 scene with objects touching all four
boundaries. Public delivery exposes demonstrations and one query input at a
time; hidden mode, Racket source, future queries and query labels remain private.

Bounded self-review:

```bash
python3 review.py run python3 generators/372fcf6aa6ad/workspace/parametric/verify.py \
  --seed-count 32 --racket-seed-count 2 \
  --out ../checks/372fcf6aa6ad/authoring-report.json
```

Native qualification:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify 372fcf6aa6ad \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/372fcf6aa6ad/qualification --summary
```
