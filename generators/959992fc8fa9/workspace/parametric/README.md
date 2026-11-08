# 959992fc8fa9 parametric family

This native finite family exposes one private episode parameter:

- `intersection_policy=different_red` — the exact canonical program. Sparse
  source pixels paint their rows and columns; cells reached by two or more
  distinct source colors become red (2).
- `intersection_policy=repeated_color_priority` — every input has exactly one
  source color occurring twice. Step A infers that color from the input. Step B
  uses it to resolve mixed intersections: it wins only where it is one of the
  reaching colors; unrelated mixed intersections remain red.

Inputs are deterministic and setting-neutral for a given seed. The adapter
supports 2–6 demonstrations and stable 1–4 query prefixes; full qualification
uses three demonstrations and all four queries. The fourth query is a 30×30
boundary-stress case with five source pixels and dense row/column propagation.
Every input contains same-color, priority-vs-unique, and unique-vs-unique
crossings, so two demonstrations distinguish both settings and six named
shortcut rules.

Run the focused finite self-audit from the packet root:

```sh
python3 review.py run python3 generators/959992fc8fa9/workspace/parametric/audit.py \
  --out generators/959992fc8fa9/workspace/parametric/evidence/self_audit.json
```

Native qualification re-executes all labels through protected Racket:

```sh
python3 review.py run python3 -m arcpuzzles parametric qualify 959992fc8fa9 \
  --demos 3 --queries 4 --out ../checks/959992fc8fa9/qualification --summary
```
