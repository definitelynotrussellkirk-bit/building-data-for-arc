# F1 — Make public-authoring stage root detection local

The first staged `public_eval_62593bfd` run passed 27 tests but its protected-label test selected the outer packet runtime because `reviewer_support.find_root` looked for canonical/catalog markers absent in an unregistered authoring stage (`checks/public_eval_62593bfd-tests/task-tests.log`). Prefer a documented stage-root marker or explicit root supplied to tests; the task-local layout fix now passes 28/28 without editing shared helpers.
