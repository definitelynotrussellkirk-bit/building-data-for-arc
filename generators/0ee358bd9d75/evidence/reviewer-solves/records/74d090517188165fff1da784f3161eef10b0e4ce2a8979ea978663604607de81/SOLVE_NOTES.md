# Exposed, visible-only solve work log

This is an authored work log, not a token-level model conversation. I previously
read and edited this task's generator and knew its rule during repair. Earlier
exposure is **yes**. During this solve I used only the preparation's public
challenge and my own Python; I did not reopen the generator, Racket rule,
canonical answers, earlier explanations, or masked query labels.

## Initial hypothesis

Full-width zero rows and full-height zero columns divide each input into a
rectangular arrangement of sections. Each output cell represents one section
in the same order. Ignore zero cells inside a section and select the most
frequent remaining color. The visible examples show unique winners; I leave
ties unsupported rather than inventing behavior.

The first example is 23x28 -> 3x3 and has single-color sections. The second is
21x19 -> 3x3 and contains small minority marks: its top-left section begins
with color 2, but output is 7, so merely taking the first nonzero cell fails.
The third is 24x20 -> 3x2 and also contains minority marks, confirming that
frequency rather than presence or scan position selects the output color.

The queries have known input shapes 23x17 and 17x20; their true outputs are
unknown to this solve. The code computes predictions without reading labels.

## Revision 1

Implemented separator extraction, per-section counters, and unique-frequency
selection in pure Python. This is my first attempted solution; there was no
earlier failed hypothesis to report. Check visible pairs and retain masked
predictions for the maintainer. A passing visible check is not a query score.
