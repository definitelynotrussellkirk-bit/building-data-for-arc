# Workspace

`reference_probe.py` is a portable review helper for `f4725b891d89`. It independently
loads public canonical pairs through `reviewer_support`, implements the public
row/column equality oracle, and extracts header entries, exact observable axes, and
simple profile tuples. Task-local tests use it instead of importing the production
rule mirror, reducing same-bug confirmation risk.

The helper exposes canonical labels and must not be opened or used during a visible-only
solve episode. Workspace drafts are never automatically selected; the selected
implementation is `../generator.py`.
