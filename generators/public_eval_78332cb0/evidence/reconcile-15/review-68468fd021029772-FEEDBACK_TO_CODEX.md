# Feedback to Codex

## F1: Biggest avoidable friction: batched Racket syntax failures omit the offending file

`arcpuzzles.review_programs` reported only `Unexpected )` when one of six supplied programs failed, so the batch had to be rerun file-by-file. Include the program path (and preferably line/column) in each parse exception; this preserves the useful batched check while making a one-character defect directly actionable.
