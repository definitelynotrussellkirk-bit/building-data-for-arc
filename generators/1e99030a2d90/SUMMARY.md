# 1e99030a2d90 — red cardinal centers

Version: **2.1.0**. Kind: `per_puzzle`. Canonical rule hash: `54991f3f258a` (unchanged).

Paint an originally blank interior cell yellow (4) exactly when its four cardinal neighbors are red (2). Preserve every other cell. Racket supplies all production labels.

The normal four-demonstration curriculum alternates canonical 10×10 and 11×11 inputs using colors 0/2 with larger color-counterexample inputs. Every default input includes a true target with diagonal context, four missing-arm negatives, an occupied center, and an edge-wrap trap. Color-counterexample inputs also contain a foreign-color cross; its color stays fixed within one family seed. The declared lesson check compares 18 finite rivals with the supplied reference labels.

Exact controls are `grid_h` and `grid_w` in 5..24, and `n_diamonds` in 1..12. The count means realized qualifying centers. This sampler reserves disjoint 3×3 motif slots: requests exceeding `floor(grid_h/3) * floor(grid_w/3)` are explicitly rejected. That is a construction restriction, not a limit of the canonical rule. Tiny or dense explicit requests may omit teaching cues and have no four-demonstration lesson guarantee.

Use one fixed seed and consecutive sample indices to assemble a family. Four demonstrations plus one query, including each holdout of those five pairs, were checked against the declared rivals; independently sampled families must not be combined under that claim. See `notes.md`, `tests/test_distribution_contract.py`, and `workspace/probe_exact_controls.py`.

Approval remains derived by the catalog from current code and retained evidence. This repair does not grant training admission or prove identifiability against undeclared rules.
