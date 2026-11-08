# Review workspace

`reference_probe.py` is an independent, reusable geometry oracle for this task.
It loads canonical pairs through the portable reviewer helper when available,
extracts panel shapes, computes rotation and dihedral keys, evaluates the
intended relation and four shortcut rivals, and exposes observable facts used by
task-local tests.

It deliberately does not import helpers from `generator.py`; this keeps the
regression suite capable of detecting shared semantic drift. The production
Racket program remains label authority.
