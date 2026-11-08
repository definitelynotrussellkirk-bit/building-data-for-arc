# Stencil-transfer family implementation plan

Goal: solve all supplied abc82100 labels with a general Racket rule, then build a matched-input two-setting family and source-bound evidence.
Architecture: detect source/paint-color tails leading toward cyan stencils; recover relative stencil offsets and apply them to remaining source-color seeds. For touching stencils with multiple tails, partition cyan by distance to the oriented tail axis. The alternate setting rotates the recovered offsets a quarter turn before stamping.
Constraints: only this assigned home; exact canonical copy; no parent data in generation; 2–6 demos; four distinct private queries; exact 30×30 stress; separate current-query projection, no hidden fields.

- [x] Tests first: supplied originals and hand-computed transfer/clipping cases. Implement independent Python model and protected Racket reference.
- [x] Tests first: matched streams, prefix stability, invalid arguments, complexity, and privacy. Implement native sampler/adapter/generator contract.
- [x] Bounded audit: attack recoloring-only, bounding-box, anchor, orientation, first-rule and first-seed shortcuts; retain and repair counterexamples.
- [x] Run protected original/preflight checks, max-count checks, source-bound causal witness/replay, public export invariance, final tests.
- [x] Self-review and package only scoped sources and compact evidence. Owner registration and acceptance remain pending.

Rulings: isolated extracted checkout; no git history is supplied. Native execution here; no subagent tool is available. Near-axis partition for touching stencils is an authored generalization; finite original labels cannot establish its universal intent.

Execution: originals and hand fixtures RED→GREEN; adapter/privacy RED→GREEN; source-drift/rival checks RED→GREEN. Bounded source-bound audit and protected execution passed. Final review: self-review (no subagent tool).

- [x] Native witness receipt schema regression RED→GREEN; regenerate exact-source preflight/audits.
