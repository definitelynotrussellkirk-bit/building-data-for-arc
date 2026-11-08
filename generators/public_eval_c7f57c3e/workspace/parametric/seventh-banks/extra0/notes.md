# c7f57c3e — scale-normalized motif exchange

## Reference and original evidence
The new general reference groups eight-connected multicolor foreground objects on a unique modal background. Every object contains the common blue (1) alignment skeleton. The greatest common divisor of blue run lengths recovers integer scale; the primitive blue origin aligns normalized colored templates, including accents outside the blue bounding box. Exactly two distinct normalized templates are exchanged at every occurrence, preserving the occurrence's own scale and blue origin. No supplied grid or answer is looked up by the rule or sampler.

Both supplied training labels and the supplied test gold match protected Racket. The public test contains three copies of one motif (including a scale-three copy) and one of the other. The source test fixture is author-private validation data only; generator.py and the adapter do not read it.

## Episode-fixed alternative and teaching
`replacement=exchange` is byte-exact to reference.rkt. `replacement=minority` counts occurrences of normalized templates, chooses the less frequent motif and stamps it at every existing origin/scale. An equal-frequency input chooses the first row-major discovered motif. The first two demonstrations use a last/large minority and then a first/small minority, rejecting first/last, area-based and largest-object selectors. The blue skeleton, not full-object bounding-box alignment, fixes placement when an accent moves to another side.

Counts are independently supported: 2–6 demonstrations and 1–4 distinct prefix-stable queries. Query presentation uses a separate controller seed, shuffles the full four-query bank, and reveals one masked input per turn without count hints. Public files contain no setting, program, future query, answer or source index. The directory/manifest remains private.

The sampler varies primitive skeletons, rotations/reflections, decoration colors and positions, scales 1/2/3, motif frequencies and spatial arrangement. The fourth query is a substantive 30×30 scene with at least 100 active cells spread across at least 25 rows and columns. Generator.py embeds its required engine for generator-only relocation; its behavior is covered by the same semantic tests and protected-Racket checks.

## Explicit grammar and limits
All foreground belongs to separated eight-connected motifs. Each motif has uniform, aligned integer blocks and the same primitive blue mask. There are exactly two normalized colored motifs. Either substitution must fit inside the canvas without colliding with another motif. Touching instances, isolated nonblue noise, nonuniform scaling and ambiguous backgrounds are outside the declared grammar. Python is a claim mirror, not the label authority. Twelve tested rivals and a finite seed audit do not prove universal identifiability or training benefit.

The causal witness preserves the input and substitutes the majority template for the measured minority template; protected Racket changes 55 output cells. Original execution, authoring preflight and reviewer replay grant neither owner qualification/acceptance nor training admission. Owner registration and source review are required before native qualification and acceptance.

## Current finite checks
44 task tests passed, plus a 64-seed audit over all five demo counts (640 episodes, 5,120 pairs) with 12 declared rivals and no harmful survivors. The audit covered eight blue-mask shapes and scales 1, 2 and 3. Protected Racket passed all three supplied original labels, both settings at two preflight seeds, 40 additional maximum-count labels and two equal-frequency boundary labels. Six generator-only relocation labels and 16 masked one-query exports passed. Both task suites also pass in a copied environment without shared original data.
