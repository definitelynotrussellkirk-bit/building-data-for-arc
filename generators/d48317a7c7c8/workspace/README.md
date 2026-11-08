# Reference and shortcut probe

The selected implementation is `../generator.py`. This directory contains reusable review support; running it does not select a new implementation or alter the canonical rule.

## Run the actual-reference probe

From the packet's `WORK/repo` directory, with Python 3.12+ and the packet's offline Racket setup:

```bash
python3 ../run_with_racket.py python3 -B generators/d48317a7c7c8/workspace/probe_review.py --out ../checks/new-semantic-probe.json
```

Use a fresh output path for changed sources. `--help` lists seed, band, and sample-count controls. The default run labels five canonical pairs, fourteen hand-built edge cases, and twelve generated inputs in each of three bands through public `Catalog.apply`, in batches of at most 64. It records exact inputs, outputs, input/output hashes, generator/rule identities, declared-witness hits, and rival disagreements. Its expected cap detector uses maximal runs plus an external-neighbor check, independently of the generator's component helper. The diagnostic Python mirror is checked against Racket; it is not used to invent reference labels.

The tool discovers the actual `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_RIVALS`, and witness declarations. It deduplicates the same callable while retaining namespace membership, records each rival's agreement on every usable canonical pair, and fails on reference/mirror/witness inconsistencies or missing generated counterexamples for canonical-fitting rivals. A non-fitting declared rival is reported, rather than itself causing failure. Extending a declared rival does not require copying a name list into the probe.

## Run the task-local tests

From the outer directory containing `review.py`, create an interpreter with pytest, NumPy, and Pillow available with user-site packages disabled, then run:

```bash
WORK/.venv-review/bin/python review.py check --stage task_tests --phase after --out ../checks/new-task-tests
```

The repository uses an isolated runtime layout. Tests call `reviewer_support.find_root(__file__)`; do not replace that with fixed parent-depth assumptions. `test_review_regressions.py` checks validation, exact override behavior, small-board feasibility, count preservation, and required distractors. `test_reference_semantics.py` checks literal edge cases and both mirrors against the selected canonical Racket program. The final review ran 69 + 20 = 89 cases.

The separately retained `counterexamples/review-e112c2eed9e98149.json` contains actual-reference examples for the strongest color shortcut, overlong components, and a bent component. The 8x8 rich example refutes all nine current rivals. Provenance points into the source-bound return evidence; outputs are copied from successful public reference calls, not from a fresh Python guess.

For lesson-level claims, use the public `lesson-census` with three demos, one query, and `--rotate-query`, then inspect both production and rotation counts. The 300-lesson result in this review is finite evidence against declared rivals. The semantic probe alone does not prove that every possible lesson is identifiable. Keep no-op/reference-domain tests separate from the productive `self_check` domain, and retain failed iterations when changing support.
