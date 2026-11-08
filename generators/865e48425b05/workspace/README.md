# Workspace tools for 865e48425b05

The selected implementation is `../generator.py`; workspace files are review tools and are never selected automatically.

- `reference_probe.py` is an implementation-independent oracle for the palette/mask rule. It contains a separately written mask catalogue, canonical-data loader, exact-axis observer, four plausible rivals, and a public-API Racket parity helper. Task tests import it so production helpers cannot make both implementation and test wrong in the same way.
- `review_probe.py` is an executable deep audit. It exhausts the complete joint exact-axis cross-product, checks every held-out query across configurable cyclic schedule starts and all three bands, verifies every declared canonical shortcut, and optionally compares the independent oracle with real Racket outputs.

From the packet root:

```sh
python3 run_with_racket.py python3 \
  generators/865e48425b05/workspace/review_probe.py \
  --out ../checks/review-probe.json --cyclic-starts 48
```

The final review run covered 3,456 exact-axis/difficulty combinations, 144 cyclic starts, 576 query rotations, and 29 Racket parity inputs with no failures. This is finite evidence against the declared rivals, not a proof of unique induction against every possible rule.

## Native parametric candidate — review-c8b8a427b8f4d43c

`parametric/adapter.py` is the promotion entry point. It exposes one setting,
`layout_policy`, with values `horizontal`, `vertical`, and `dominant_axis`.
`horizontal` returns the exact canonical Racket source from `canonical.rkt`.
`prototype.py` constructs deterministic 2–6-demo/1–4-query episodes;
`audit.py` performs the retained named-rival, protected-Racket, public-turn, and
causal checks. `promotion.json` is the native contract, and
`parametric/evidence/manifest.json` binds the qualified source/evidence inventory.

Retained reviewer evidence lives under `WORK/checks/865e48425b05/`, including
`qualification/qualification.json`, its sibling `execution.json`, and the native
sequential witness at `causal/witness.json`. These are reviewer artifacts only;
owner integration and fresh acceptance replay remain mandatory.
