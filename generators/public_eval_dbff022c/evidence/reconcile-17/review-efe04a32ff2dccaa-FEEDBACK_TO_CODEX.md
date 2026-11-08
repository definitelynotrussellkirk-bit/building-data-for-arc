# Feedback to Codex

## F1: Biggest avoidable friction: copied-runtime module contamination

The reviewer task-test wrapper can inherit `arc_repl` modules imported from a different checkout, causing protected-Racket tests to execute against the wrong runtime even though the copied source is correct. The task tests had to use `_local_imports(root/'shared/runtime', task_parametric_home)` explicitly; the wrapper should purge or isolate matching modules before every copied-checkout test run.

## F2: Make public-projection validation part of authoring preflight

The authoring preflight validates source and labels but does not itself require a four-query private bank, independent presentation ordering, single-query export, or mutation-invariance proof. Adding an opt-in adapter hook that emits and checks all sequential public views would remove a separate custom audit step and catch prefix-only query exposure immediately.

## F3: Add a reusable semantic-rival census hook

The widened `dbff022c` audit found three real teaching shortcuts only after custom rivals were added. Let `review_public_creation preflight` optionally load a task-local `rivals.py`, record demo survivors and query disagreements, and bind that finite census into the preflight receipt; this would standardize the reusable audit built here without implying universal uniqueness.
