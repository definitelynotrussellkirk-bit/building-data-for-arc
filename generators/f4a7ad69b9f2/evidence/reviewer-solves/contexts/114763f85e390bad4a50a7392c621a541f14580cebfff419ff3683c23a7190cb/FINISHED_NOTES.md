# Post-repair visible-only solve notes

This is a human work log. I had already seen the task rule while reviewing the
generator, so this episode is **exposed**, not blind. During this solve I read
only `solve/challenge.json` and my own files; I did not consult the generator,
Racket source, private labels, reference solutions, or earlier solve text.

Visible-example observations:

1. Each input contains three separated monochrome 4-connected objects on zero.
2. The output consists of the tight crops of those objects, top-aligned, with
   one all-zero column between crops.
3. Crop order is ascending bounding-box width, then height. The examples with
   equal dimensions require comparing the complete row-major colored crop
   lexicographically rather than using input position or color alone.
4. Output height is the maximum crop height; output width is the sum of crop
   widths plus two separator columns.

Planned first revision: extract same-color 4-connected components, crop each,
sort by `(width, height, flattened crop)`, and render top-aligned with one zero
column. No deliberate negative or diagnostic revision is needed because the
visible examples support one consistent rule.

Revision 1 executed successfully and matched all 5/5 visible demonstrations.
I stopped because the rule is fully specified by those examples, the
implementation covers both test inputs, and further revisions would be
manufactured rather than evidence-driven. Masked-query correctness remains
withheld for maintainer scoring.
