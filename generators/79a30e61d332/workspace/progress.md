# Inline repair ledger — 79a30e61d332

- Baseline: generator v3.1.0, battery 7 pass / 1 advisory / 4 fail.
- Root causes: missing authority pin; stale selected target text; dishonest/dead axes; unknown overrides accepted; no semantic contract; generator collapses canonical 3–6-key, two-axis rule to exactly two keys on one axis.
- Strongest canonical-fitting rival: match 3x3 tiles by row-sum tuple instead of exact mask. It fits all four labeled canonical pairs.
- Plan: RED task tests; rewrite sampler/contract; sync selected target text; GREEN task tests; battery/census; fresh visible-only solve; audits; reports; fresh-packet patch replay; package.
- RED: 89 failed / 8 passed against v3.1.0 (`checks/test-red.log`).
- GREEN focused suite: 97 passed (`checks/test-green-attempt1.log`).
- Ruling: support every layout_profile × n_keys × key_cells combination rather than declare vertical/high-key incompatibilities; profile classification is based on actual non-key bridge tiles, so contiguous extra keys do not create a false second axis.
- Semantic RED: required query rotation exposed seed `84165169887915`, sample 35, where a nominal mixed layout had no axis-unique vertical bridge (`checks/test-red-mixed-axis-overlap.log`).
- Ruling: a mixed profile must have at least one bridge tile unique to each axis; merely having both aligned-pair types is insufficient.
- Final focused suite: 98 passed; real Racket parity covers 4 canonical + 18 generated inputs.
- Final battery: 12/12 green with required rotations; semantic gate 600/600 strict, 6/6 witnesses, 6/6 rival claims, 12/12 lessons, 0/48 ambiguous rotations.
- Census: 300/300 production lessons and 0/1200 ambiguous query rotations; 1200 unique inputs (`checks/lesson-census.json.gz`).
- Fresh original-packet replay: `git apply --check`, apply, source-hash match, and 98/98 portable task tests all passed.
- Final generator SHA-256: `f5e6d7a5ef750095ba68968cd39c3da98bfdf167c88307e509b6c7d22e8dd5aa`.
