# Native resources

`adapter.py` loads only adjacent `engine.py`, `canonical.rkt`, and `minority.rkt`. `canonical.rkt` is byte-identical to ../../reference.rkt. `wrong_frequency.rkt` is a private causal ablation, not an admitted setting.

From the packet root, run the task tests via `review.py run python3 -m pytest --import-mode=importlib generators/public_eval_c7f57c3e/tests -q`. Run `audit_lessons.py --seeds 64 --out ../checks/public_eval_c7f57c3e/audit.json` under the same wrapper to audit every demo count and the finite rival set.

`presentation.project` requires the complete four-query private bank before shuffling and taking a prefix. It returns private rows containing source indices; expose only an individual row's serialized `bytes`. `write_batch` verifies public schemas/identities and rejects duplicates before writing. The bank, row list and directory listing are controller-private.

Runtime: Python 3.12+ with the repository reviewer_support and puzzle_generators runtime; independent labels require the bundled protected Racket runtime. The base generator is self-contained when relocated without this directory. See ../../notes.md for the grammar and evidence limitations.
