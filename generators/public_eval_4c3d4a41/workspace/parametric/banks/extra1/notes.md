# public_eval_4c3d4a41 authoring notes

This is an unapproved public-evaluation authoring prototype. The general Racket
reference is checked against every supplied training pair and supplied test gold.
The task-local native adapter exposes two finite settings over matched inputs,
2--6 demonstrations, and a private four-query bank. Public views reveal one
query at a time and contain no setting, program, answer, future-query, or total-
query metadata.

The setting-dependent second step is intentionally based on an intermediate
created by the first step. `workspace/parametric/wrong_order.rkt` holds a
source-level counterfactual; `workspace/parametric/audit.py` executes both
programs through protected Racket and writes an admission-schema witness.
Bounded rival checks are evidence against the declared shortcuts only, not a
claim of universal identifiability.
