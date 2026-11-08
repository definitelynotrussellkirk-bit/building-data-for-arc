# General feedback

**F1: State the ordinary generator worker signature in the public-creation duties.**

The preflight invokes `generate(seed=..., sample_index=..., difficulty=...)`, while the prose contract only says to create `generator.py`; making that exact keyword interface explicit would prevent avoidable late failures. Evidence: `checks/public_eval_e87109e9-tests/task-tests.log` and `checks/public_eval_21897d95-tests/task-tests.log` include focused worker-interface coverage.

**F2: Use the strict one-expression Racket parser in every authoring execution path.**

A protected runtime path can execute a valid leading `rule!` while overlooking trailing syntax, whereas the public-creation preflight correctly requires one complete expression. Reusing the preflight parser at the earliest local rule check would surface structural errors before expensive episode execution. Evidence: `checks/public_eval_e87109e9/preflight/preflight.json` and `checks/public_eval_21897d95/preflight/preflight.json` record the strict program-syntax gate.
