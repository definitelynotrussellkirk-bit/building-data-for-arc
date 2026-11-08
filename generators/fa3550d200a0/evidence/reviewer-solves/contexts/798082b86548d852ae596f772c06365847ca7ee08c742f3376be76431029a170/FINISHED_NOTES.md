# Exposed post-repair solve work log

Earlier rule exposure: **yes**. I authored the generator repair and inspected
its reference before this phase. Reference consulted during this solve: **no**.
From preparation onward I read only the public solve README/challenge and my
own attempted Python code. This is an exposed attempt, not a blind evaluation.
These notes are a concise authored work log, not a token-level model transcript.

## Visible observations and hypothesis

Example 0: input 30×25, output 9×8. The large color-8 rectangle becomes the
output. Its color-3 marker acquires the two vertical payload cells of the outside
color-3 object, including the cell two steps from the marker. The color-9 object
has diagonal-only connections, which also appear in the output. The unmatched
color-5 object is absent. This supplies direct evidence against a centered 3×3
window and a four-neighbor-only component interpretation.

Example 1: input 16×24, output 11×9. Three colored marks identify translated
copies of their matching outside shapes, without rotating those shapes.
Example 2: input 26×24, output 10×12. The rectangle is color 1, so the canvas
role cannot be a fixed color-8 rule. Its four matching markers receive their
payloads while the extra color-9 object is ignored.

Candidate: identify the dominant nonzero color and crop its bounding rectangle;
find eight-connected nonzero objects outside that rectangle; match each unique
colored marker to the same-colored inside mark; translate and stamp the full
component. Leave unmatched pieces out. I wrote a standalone standard-library
implementation, without importing the generator, reference, or prior solutions.

The masked query inputs are 26×24 and 24×28; their output dimensions and answers
are unknown until an independent scorer evaluates them. I will not infer a
masked-query score from visible-example success.

## Revision 1

One candidate was written. First perform a public-only Python comparison on
the three visible labels, then use the required visible-only solve check. Any
feedback and stopping decision will be appended before the finish snapshot.

Public-only Python comparison: all 3 visible pairs match exactly. No revision was needed before the official check.

Official revision-1 check completed: 3/3 visible examples passed; execution completed; both masked query scores remain unknown. I stopped after the first successful candidate because the visible endpoint, diagonal, unmatched-marker, and changing-canvas-color cases support it. Earlier authoring exposure remains yes; no reference or generator was reopened during this solve.
