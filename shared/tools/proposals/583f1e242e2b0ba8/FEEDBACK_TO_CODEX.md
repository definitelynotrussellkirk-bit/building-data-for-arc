# Feedback to Codex

The packet's journaled commands and public/private evidence rules were strong. Two workflow improvements would make future reviews more robust:

1. Make stage-by-stage battery execution the documented default, with a single command that resumes individual stages. The monolithic battery can be externally interrupted during a long profile stage even after earlier stages have passed, which obscures useful receipts.
2. Ship a minimal parametric-prototype template containing a public projection, private query labels, a same-input/different-setting witness, and a verifier manifest. That would reduce repeated scaffolding while preserving the strict separation required for review.

This run also experienced a tool-container reset after the first complete implementation. The archive's deterministic assignment draw and journal format made recovery possible; a compact `review.py checkpoint export` command would make that recovery faster and less error-prone.
