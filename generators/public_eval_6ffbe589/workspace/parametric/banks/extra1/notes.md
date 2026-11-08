# Current authoring work — 6ffbe589

Unapproved public-evaluation family. No owner registration, source approval,
native acceptance or training admission is claimed.

## Design and implementation plan

The input contains concentric, disjoint color masks forming a square picture,
and detached straight monochrome tally bars. Recover the square around the
largest multicolor component; require concentric nonoverlapping radial color
bands, a tight square extent, and at most one straight external bar per color.
The count outside the square determines that color's clockwise quarter turns.
Counts are reduced modulo four. Missing bars mean zero turns. Output only the
rotated square. The alternative reverses rotation direction, not the grammar.

Using the whole foreground bbox would include instructions; using only the
largest connected component would lose detached parts of the test picture.
The selected centered-square recovery handles both while rejecting ambiguous
or malformed Python inputs explicitly. The Racket rule returns the input on
out-of-grammar scenes; those scenes are not sampled or claimed as taught.

Implementation sequence: literal official-pair and focused failing tests;
independent Python and general Racket implementation; constructive sampler and
native contract; finite executable-rival/self-review; protected preflight,
source-bound witness and sorted hash-ID single-query exports; staged tests and
relocation check. All changes stay inside this assigned task home.

Review focus: disconnected outer masks; missing and >4-count bars; even centers;
wrong-direction/fixed-count shortcuts; stale evidence and private-field leaks.

Test correction: directory enumeration order is filesystem-defined, not write
order. Export verification records actual writes while retaining real filesystem
IO, and checks byte-identical files after reversed private enumeration.

## Self-review repair and limits

The old two-demo schedule used squares of sizes 16 and 18 and only four colors.
Protected rivals that stopped rotations above size 20 or ignored the fifth
(highest-numbered) color fit both demos and failed a legal query: both retained
match vectors are [true, true, false]. The second demo now has a 22-square, five
colors and a nonzero rotation of the highest color; it occupies a substantive
30x30 canvas. This is a constructive repair, not a larger demo-count requirement.
See checks/public_eval_6ffbe589/teaching-gap-before.json and the focused regression.

The square-center recovery assumes the largest mixed component is centered on
the nested picture, with disjoint radial color bands and straight detached tally
bars. This fits all four supplied labels and every generated grammar branch; it
is not a general detector for arbitrarily disconnected, off-center pictures.
The generated maximum picture is 22x22 inside a 30x30 input because instructions
also need space. Both directions are episode rules; only clockwise is the parent.
The bounded rival list is not a proof of universal identifiability.

One initial exhaustive 32-seed prefix run exceeded a 200-second tool limit and
produced no receipt. The retained audit uses full API-prefix coverage at seeds
0..3, two selected prefix requests at the remaining seeds, and minimum-lesson
rival checks across all 32 seeds. No timed-out run is counted as passing.
