# Parametric square-tally block order

The input grammar and square-count reasoning are shared across both settings.
The byte-exact canonical `construction` rule identifies solid square components,
computes adjusted counts, converts those counts into active-size glyph layers,
and emits the layers in construction order. `reverse_construction` emits the
same input-derived layer list in reverse order. The private setting never affects
input sampling.

The adapter supports 2–6 demonstrations and 1–4 queries. The first two
constructive demonstrations cover noncanonical size sets, both states of the
smallest-key condition, and same-color distractors. Four queries are privately
shuffled before a prefix is selected and include a substantive 30×30 scene.

Focused tests:

```bash
python3 review.py task-tests d0a85a878975 --phase after --out ../checks/d0a85a878975-tests
```

Bounded self-audit:

```bash
python3 review.py run python3 generators/d0a85a878975/workspace/parametric/audit.py \
  --out ../checks/d0a85a878975/audit.json --seeds 16
```

This is reviewer-ready authoring evidence only; owner source review, native
qualification/acceptance, and any training admission remain separate gates.
