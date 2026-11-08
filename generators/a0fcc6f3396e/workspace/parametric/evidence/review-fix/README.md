# Prototype complete-episode coverage correction

The focused regression checks the real evidence writer with explicit synthetic
label-worker responses. It exercises single-setting episode populations for
both output colors, verifies that their public and private episode receipts are
retained, and requires a partial verdict with the missing complete-episode
setting identified. It does not stage a runtime or verify Racket labels.

Actual Racket semantics remain covered by the existing executed-label test and
retained authoring runs. The task owner will perform final source verification
after the current large-runtime work finishes.

The red and green logs and `verification.json` in this directory record the
focused test commands, actual exits, source identities, and the test boundary.
