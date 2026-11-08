# Post-repair solve: exposed earlier, visible-only during this attempt
Earlier exposure: YES. I reviewed and repaired this generator and read its reference before beginning this separate solve. I have not reopened generator code, the Racket rule, private labels, canonical helpers, or previous solutions during this solve. This attempt is not blind.

Visible examples have input/output dimensions 19x19->19x19, 17x21->17x21, and 18x19->18x19. The two queries are 19x19 and 21x18 with unknown outputs.

Hypothesis from visible changes: the cyan rectangle sends horizontal rays through each of its rows and vertical rays through each of its columns. Rays paint black and red cells yellow, pass through red rectangles, and stop at other nonzero colors. Each row/column stops separately rather than clipping the entire arm. The cyan emitter and opaque objects keep their cells.

The generalized middle demonstration contains colors 6,7,9 and refutes a blue-only blocker rule. Its top blocker clips columns 2..5 while columns 6..7 continue; that distinguishes per-ray from whole-arm clipping. Red is overwritten only along the cross. Implemented direct outward scanning from the cyan bounding box, without the authoring generator's object-analysis helpers.

Revision 1 is the first genuine solution attempt. The visible-only checker decides demonstration agreement; query correctness remains withheld. Stop after all three visible examples match and both masked query executions complete. No manufactured negatives.
