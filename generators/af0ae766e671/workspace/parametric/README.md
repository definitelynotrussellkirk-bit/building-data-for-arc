# `af0ae766e671` native global-selection family

This task-local family preserves the selected stacked-panel XOR rule exactly and
adds one nearby episode-fixed rule over matched inputs.

| `selection` | Meaning |
|---|---|
| `xor` | Canonical/default: paint every aligned position occupied in exactly one panel. |
| `sparser_panel_only` | Count occupied cells in both panels, choose the uniquely sparser panel, and paint only exclusive cells belonging to that selected panel. |

The sampler constructs all four aligned occupancy states and unequal panel
occupancy totals. It supports independent 2–6 demonstration and 1–4 query
requests with stable prefixes. Every maximal episode has four distinct queries;
the fourth is a dense 30×30 stress case. `public_turn` reveals one query input at
a time without settings, programs, answers, future queries, or count hints.

The sequential dependency is global: Step A derives both occupancy totals and the
selected panel; Step B must consume that selected-panel identity to decide which
exclusive state is painted. `self_audit.py` checks declared rivals and executes a
denser-panel wrong-intermediate counterfactual through protected Racket.

`legacy_27_settings.py` retains the earlier exploratory `operation × output_color`
prototype and its audit format. Compatibility wrappers in `prototype.py` keep the
old focused tests runnable without adding those 27 settings to the promoted native
parameter domain.

From the packet outer directory:

```bash
python3 review.py run python3 generators/af0ae766e671/workspace/parametric/self_audit.py \
  --out generators/af0ae766e671/workspace/parametric/evidence/replay-new
python3 review.py run python3 -m arcpuzzles parametric qualify af0ae766e671 \
  --seed 0 --seed 17 --demos 2 --queries 4 \
  --out ../checks/af0ae766e671/qualification-new --summary
python3 review.py task-tests af0ae766e671 --phase after \
  --out ../checks/af0ae766e671-tests-new
```

These are reviewer artifacts only. Owner exact-source acceptance and any training
admission remain separate.
