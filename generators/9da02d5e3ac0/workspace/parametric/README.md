# Row fill, then vertical bridge

`finish_rule=row_fill_only` is the exact selected canonical program. The
alternative keeps that first stage and then bridges zero gaps in a completed
column only when every nonzero/non-5 signal in the column has one shared color.
Inputs are identical across settings; outputs alone reveal the episode-fixed
rule.

## Causal dependency

1. **A:** replace each color-5 cell with its row's first non-5 value.
2. **Intermediate:** the completed grid, including signal-colored endpoints
   that were still 5 in the input.
3. **B:** inspect each completed column and bridge zeros strictly between its
   first and last signal only when all signals share one color.

B cannot identify the derived bridge endpoints or their color before A. The
bounded protected-Racket causal witness substitutes raw-input columns for the
completed intermediate and changes 107 cells in the retained 30x30 case.

The adapter accepts 2–6 demonstrations and 1–4 independent, prefix-stable
queries. Its fourth query is a substantive 30x30 input with dense color-5
material and content touching every boundary. `public_turn` exposes all visible
demonstrations and exactly one query input, with no setting, program, answer,
future query, index, or total-query hint.

Every generated lesson member contains a literal-zero row key plus a color-5
cell and later colored signal. This directly rejects the tempting
"first nonzero" replacement for the canonical first-non-5 rule, including in
the minimum two-demonstration prefix.

## Reproduce from the packet outer directory

```bash
python3 review.py run python3 -m pytest -q \
  generators/9da02d5e3ac0/tests/test_parametric_vertical_bridge.py

python3 review.py run python3 \
  generators/9da02d5e3ac0/workspace/parametric/audit.py \
  --seed 19 --demos 2 --queries 4 \
  --out ../checks/9da02d5e3ac0/self-audit-fresh

python3 review.py run python3 -m arcpuzzles parametric qualify \
  9da02d5e3ac0 --demos 3 --queries 4 \
  --out ../checks/9da02d5e3ac0/qualification-fresh --summary
```

The audit executes both settings and eleven finite shortcut programs through
the packet's protected Racket runtime. It is bounded evidence, not a uniqueness
proof. Qualification is reviewer evidence only; owner integration, fresh
acceptance, and any training decision remain separate.
