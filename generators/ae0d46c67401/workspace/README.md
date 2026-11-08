# Workspace

`reference_probe.py` is the reusable, source-independent qualification helper for
this task. It can load canonical pairs through `reviewer_support`, compute an
independent overlay-with-transpose oracle, recover every advertised axis from
pixels, load an arbitrary candidate generator, and query the public Racket
authority. The task-local pytest suite imports it both from this checkout and from
the portable staged runtime.

The selected implementation is `../generator.py`. Workspace helpers are review
tools and are never automatically selected as production generators.
