# Supplemental verification

The selected implementation is `../generator.py`; this workspace never overrides it.

From the extracted review packet root:
```sh
python3 run_with_racket.py python3 generators/28268c57c367/workspace/review_probe.py --seeds 20 --out ../checks/boundary-cyclic-probe.json
```

The public wrapper runs from repo. The script uses reviewer_support.find_root and the public Catalog.apply API; it resolves both library and staged task layouts. It checks the complete 504-setting legal joint boundary product across three bands and both profile positions, then labels five consecutive examples per seed/band with Racket and examines every cyclic start modulo two and every holdout from a four-pair window. Actual CANONICAL_SHORTCUTS and LESSON_COMPETITORS declarations are used, with input-mutation guards and full failure reproducers.

Output distinguishes draws, unique inputs and overlapping lesson views; positive label-population and authority-response digests bind the run. It records all failed cases, if any, and exits nonzero. This is a direct-generator supplement, not a production-sampler replacement or universal identifiability proof. Run the main lesson-census with 100 lessons per band separately. The probe intentionally fails when this task's period-two/three-demo contract changes, requiring explicit adaptation rather than stale certification.
