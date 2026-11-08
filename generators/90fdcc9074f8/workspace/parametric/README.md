# Parametric panel-vote family

`vote_policy=majority` is the exact canonical rule: repair three noisy panels by
keeping cells marked in at least two panels, then compute component-wise onion
depths and crop. `vote_policy=unanimous` requires all three panels before the
same depth stage. The repaired mask is the input-dependent intermediate consumed
by the onion-layer step.

The deterministic sampler supports 2–6 demonstrations and 1–4 matched queries.
It includes two-vote boundary cells and one-vote distractors, selects omissions
only when the unanimous mask stays connected, and stresses a substantive 30×29
input (three 30×9 panels plus separators).

From `WORK/repo`, run the focused checks through the packet runtime:

```sh
python3 ../run_with_racket.py python3 -m pytest -q --import-mode=importlib \
  generators/90fdcc9074f8/tests/test_parametric_vote_policy.py
```

The default program is preserved byte-for-byte. This prototype and its evidence
do not approve the base, accept the family, or admit generated data.
