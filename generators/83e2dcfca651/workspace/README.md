# Workspace

`reference_probe.py` is the portable independent geometry oracle used by the task tests. It loads canonical pairs through `reviewer_support`, observes the five exact axes, computes signed/absolute-vector outputs, measures shape/component diversity, and can batch-check inputs against the public Racket authority.

The selected implementation is `../generator.py`. Workspace helpers are evidence and test support; they are never automatically selected as the generator.
