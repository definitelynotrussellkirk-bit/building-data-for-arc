# Exposed final-generator solve

This is a concise work log, not a captured token-level model trace. Earlier rule
exposure: **yes**, from the preceding generator review. During this solve I opened
only the public README/challenge and my own Python implementation; I did not
consult generator source, Racket source, prior solution notes, or private labels.

## Revision 1 — intended solve

The three visible pairs have shapes 9×9, 19×22, and 7×9, with equal input/output
shapes. Two masked query inputs have shapes 15×13 and 6×9; their true output
shapes and labels remain unknown to me.

I used the hypothesis that opposing boundary 4s select an entire row or column.
On their union, exchange 0 with 8 and 6 with 7 once, leaving 4 fixed. Example 0
shows the reverse substitutions, example 2 the forward substitutions. Example 1
shows both directions within a single input, both orientations, an intersection,
and isolated endpoint markers that do not activate a full line.

The implementation builds the two selected index sets from the input and applies
one substitution with an OR condition. No query-specific coordinates or colors
were inferred from hidden answers. I am submitting one genuine solution attempt;
I have not manufactured a failed revision or teaching negative.

## Verification and stopping rule

Run the supported visible-example check. If it reports all visible examples
correct and both queries executable, stop and preserve the masked predictions
without claiming they are correct. A finite visible pass does not prove a unique
rule, and earlier exposure makes this an author solve rather than a blind test.

The actual first check exited 0: all three visible demonstrations matched and
both masked query executions succeeded. There was no failed solution revision.
Masked-query correctness remains unknown. I stopped after this passing visible
check and retained this original attempt and its predictions for maintainer scoring.
