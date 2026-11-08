# Workspace

The selected implementation is `../generator.py`; workspace drafts are never automatically selected.

The reusable curriculum audit is encoded as executable task-local tests in `../tests/test_curriculum.py`. In particular, `test_every_sliding_window_has_redundant_two_arm_evidence` exhausts all 12 cyclic schedule starts for easy, medium, and hard, then holds out each of the five generated pairs in turn. Run it through the packet wrapper so the selected source is copied into a portable runtime:

```bash
cd repo
python3 ../run_with_racket.py python3 -m pytest -q generators/563e1df172df/tests/test_curriculum.py
```

The source-bound production census is retained as `checks/lesson-census-after.json` in the review return.
