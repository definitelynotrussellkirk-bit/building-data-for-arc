# Exposed post-repair solve — work summary

This is an assistant-authored work log, not a token-level trace. I had earlier
rule exposure while repairing the generator. During this fresh solve phase I
read only the preparation tool's visible examples and query inputs; I did not
open the generator, Racket source, reference solutions, earlier solution
explanations or private labels. The preparation used final generator hash
0477dc50fdff9ac43529ebbddd8173ac0641eaf0311929f51d51439040493e69.

The four visible pairs have shapes 20x20 to20x20, 14x15 to14x15, 20x20 to20x20,
and13x9 to13x9. The two queries have inputs20x20 and19x11; their outputs are
unknown. The public README presents actual dimensions before every grid.

## Revision 1 — attempted solution

I implemented the rule consistent with the displayed pairs: collect the row
and column coordinates of zeros from the original input, then clear their
union while preserving every color2. Unselected cells retain their original
values and the shape stays unchanged. Computing both coordinate sets before
writing output prevents newly created zeros from selecting additional lines.

The implementation is standalone Python and imports no generator or reference
helper. It is submitted as a genuine solution attempt. No failed attempt or
deliberate negative was manufactured. The public checker will compare the four
visible outputs and check query execution without revealing hidden correctness.
