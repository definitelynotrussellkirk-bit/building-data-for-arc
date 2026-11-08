# Apply the Transform Script — 8096ecc43d5a

Read nonzero instruction cells in row 0 from left to right. Crop the connected,
monochrome motif below the blank separator, then apply every instruction to the
current result: 1 rotates clockwise by 90 degrees; 2 reflects left/right;
3 rotates by 180 degrees; 4 reflects up/down. The output is one final crop.

Code order and repeated codes affect the answer. Zero cells are ignored, including
leading and internal gaps. The motif's color is preserved and may coincide with
an instruction color; its position below the top row identifies its role.

The sampler varies canvas size, script length, motif color, shape, size, and
placement. A seed-stable four-pair schedule provides one singleton, two composition
witnesses, and one unrestricted script. Three demonstrations and one query are
checked against twelve declared rivals, including all three incorrect constant
D4 code maps fitting the four canonical labels. These finite checks do not establish
universal identifiability or cover every override-based lesson assembly.
