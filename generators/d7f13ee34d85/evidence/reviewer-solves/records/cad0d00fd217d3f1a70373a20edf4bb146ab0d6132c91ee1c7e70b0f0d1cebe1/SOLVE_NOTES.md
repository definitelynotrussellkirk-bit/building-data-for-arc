# Exposed solve work log — revision 1

This is a human-readable assistant work log, not a token-level model trace. Earlier rule exposure: yes, from the generator review. Since starting this fresh solve I have read only the public preparation output, solve/README.md and visible challenge; I have not reopened generator or Racket source, reference solutions, previous solver notes, or private labels. Preparation automatically displayed provenance including named rival checks; this metadata exposure is recorded and is not treated as an independent blind discovery.

Visible example 0 is 13×26 in and out. Four hollow rectangular frames stay fixed; the loose motifs move into them. Interior areas are 4,12,14,15. Motif cell counts are 2,4,6,7. Matching these ranks explains why the six-cell color-5 rectangle goes into the tall color-4 frame, while the seven-cell motif goes into the larger-area, shorter color-9 frame. Ranking by frame height would disagree.

Visible example 1 is 13×18 in and out. Three differently positioned frames share color 1 and must remain separate connected components. The three-cell horizontal color-9 line goes into the smallest interior. It overwrites a left-border pixel: centering a width-three motif into width two uses a negative left offset. Keeping all placement offsets nonnegative would disagree with the visible output.

Visible example 2 is 16×23 in and out. The motifs start above the frames, so the transfer is independent of upper/lower placement. Five-, six-, and seven-cell motifs go into interiors of areas 8,14,16. Their original orientations and colors are retained. The five-cell motif again overwrites a border because its width exceeds the assigned interior by one.

Hypothesis: identify monochrome cardinal components; separate exact hollow rectangular borders from loose motifs; sort frame interiors by area and motifs by cell count; pair ranks and center each motif by floor division in each coordinate. Redraw frames and transfer motifs onto a zero canvas, allowing a transferred pixel to replace a border. The program uses only Python and reads no project files.

Alternatives considered from the visible examples: sorting frames by height/perimeter fails example 0; clamping centering to the interior fails examples 1 and 2; assigning by initial position fails the independent ordering and the upper/lower swap. These are reasoning comparisons, not fabricated failed solution attempts.

Two query inputs are visible (14×20 and 19×23); their outputs are unknown. This first implementation will be submitted to the visible-only checker. Private-query correctness cannot be inferred from its feedback. Remaining limits: finite demonstrations, no evidence here for tied ranks, multiple foreign objects in a motif crop, or arbitrary malformed inputs.
