# Feedback to Codex/tooling

1. `review_public_creation preflight` reports only `Generated query label mismatch` when a generated protected-Racket label differs from the adapter oracle. Please include setting, seed, split/pair index, and first differing cell/value. The faa9f03d port required a separate harness to discover that horizontal and vertical additions were being evaluated in different within-round states.

2. `review_witness template` intentionally selects a nondefault episode, but an adapter's `counterfactual_program(settings)` can accidentally return the same program for that nondefault setting (both adapters here initially did). `build` correctly rejects this, but the template could detect same-program hashes and either choose an alternate rival automatically or emit a targeted diagnostic before protected execution.
