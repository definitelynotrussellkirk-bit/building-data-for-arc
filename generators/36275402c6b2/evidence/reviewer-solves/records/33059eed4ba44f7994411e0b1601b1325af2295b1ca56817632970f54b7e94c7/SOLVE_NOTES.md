# Post-repair visible-only solve work log

This is an assistant-authored work log, not a token-level conversation trace.
Earlier exposure: yes, the task's generator and Racket rule were examined during
repair. During this solve I opened only the prepared visible presentation and
wrote independent Python; no generator, reference source, previous solution
notes, or private query labels were consulted.

## Revision 1 — main-object crop and directed external keys

Example 0 transforms an 11x15 input into a 6x6 crop: external (9,6) and
(8,2) pairs explain replacement 6->9 and 2->8. Example 1 is a 14x13 input
with a 6x4 output; its (7,1) key is alongside the crop, and the source1
on the crop's left border changes to7. Thus external keys must be searched
on all sides, and mapped pixels on the crop border must also change.
Example 2 is 13x13 -> 6x5 and uses three independent substitutions.

The program locates the largest four-connected same-color nonzero component,
uses its bounding box for the output, interprets external horizontal pairs
left-to-right as (replacement, source), and applies that map to every crop
cell. A new grid is returned. No deliberate wrong revision was submitted.
Remaining uncertainty concerns configurations absent from the visible examples;
private query correctness is withheld.
