# Feedback to Codex

## F1: Biggest avoidable friction: parser-only Racket validation can accept code the protected runtime rejects
`review_programs` initially accepted a balanced `for*/list`/internal-`define` form that failed during real preflight macro expansion. A concrete mitigation is to make the lightweight rule validator also compile/evaluate each form in the same protected Racket frontend (without running task data), so macro-level syntax errors are caught before expensive preflight.
