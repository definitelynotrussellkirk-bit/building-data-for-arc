# ffc1598119d4

0-bg grid (size varies) laid out as ONE color-9 SOURCE FRAME plus 1-5 color-8 TARGET FRAMES (all square, interior k in 3-4), arranged in a grid of slots. The source frame's interior holds a random MULTICOLOR pattern (2-4 colors from {1..7}). Each target frame has a COMMAND CELL directly above its top-left corner with a value in {1..4} (1=identity, 2=rotate-CW, 3=rotate-180, 4=flip-UD). Rule: extract the 9-frame interior as the SOURCE. For EACH 8-frame, read the command above its top-left corner, TRANSFORM the source by that code, and PAINT the result centered in the target's interior (clearing it first). The frames, command cells, and source stay. Net: every target frame fills with a transformed copy of the multicolor source.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
