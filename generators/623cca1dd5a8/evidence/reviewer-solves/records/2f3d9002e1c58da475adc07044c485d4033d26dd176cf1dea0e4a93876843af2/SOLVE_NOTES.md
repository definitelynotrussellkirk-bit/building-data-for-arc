# Exposed solve work log

This is a reviewer-authored work log, not a token-level conversation trace or an
independent blind solve. Earlier exposure: yes. I reviewed and repaired this
task's generator and read its Racket rule before preparing this episode. During
this solve I opened the public challenge, this solution file and these notes;
I did not reopen the generator, rule, reference solution or private query labels.

## Revision 1: component rectangle borders

Visible example 0: Input: 8 rows × 14 columns. Output: 8 rows × 14 columns.
Two separate color-5 shapes become separate rectangular outlines. The left box
spans rows 1..4 and columns 0..4; its interior pixels disappear and the missing
bottom-right boundary is filled. This visible example rejects a single bounding
box over every occurrence of color 5, copying the input while adding borders,
and filling the entire bounding rectangle.

Visible example 1: Input: 8 rows × 8 columns. Output: 8 rows × 8 columns.
The 3-by-2 and 2-by-3 bounding boxes look filled because every cell is a border
cell. Visible example 2: Input: 10 rows × 9 columns. Output: 10 rows × 9 columns.
Repeated colors again keep their disconnected objects separate.

I implemented same-color orthogonal flood fill, then the outer row and column
of each component's bounding box on a fresh zero canvas. This preserves canvas
size, handles boxes touching an edge, and naturally handles thin rectangles.
The examples do not distinguish four-neighbor from eight-neighbor connectivity
on diagonal contacts, but the displayed queries have separated components for
which that choice does not change the grouping. I did not claim universal
identifiability from these examples.

Query 0: Input: 9 rows × 9 columns. Output: unknown.
Query 1: Input: 8 rows × 8 columns. Output: unknown.
The checker will assess visible examples and execution only. Masked query
correctness remains unknown to me.

No failed solution has been manufactured. One patch application first failed
because I guessed the placeholder text incorrectly; it changed no source and
was not a solver revision. I read the placeholder and applied the same intended
implementation successfully. Next: record revision 1 with the official checker.
