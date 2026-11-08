# 446ef5d2 — current authoring decisions

## Design and execution plan
The three-cell L marker identifies a fixed corner of a fragment and therefore
of the final rectangle. Remove the marker, then translate (never rotate)
multicolored fragments into an exact rectangle with a uniform outer border and
a connected graph of matching colored contacts between fragments. Other
incidental seams may cross a true color boundary. Admit only a unique output.
Preserve all original pixels, except the marker, in canonical `assembly` mode.
Alternative `largest_region` mode assembles first, computes same-color connected
regions excluding the border color, and recolors every maximum-area region to
the marker color. Regions may cross many fragment seams: their sizes are not
available by measuring raw disconnected fragments.

Plan: (1) regression tests on all four original labels, then general solver;
(2) constructive varied jigsaws, portable ordinary generator and native adapter,
count/privacy tests, and teaching rivals; (3) protected-Racket parity, authoring
preflight, source-bound wrong-intermediate witness, exports; (4) final source
self-review and clean reconstruction. Work only inside the assigned home in this
isolated extraction. No shared source or original data changes. No approval,
owner qualification, acceptance or training admission is claimed.

Rulings: author this design directly, as requested; no remote branch operation.
Independent reviewer unavailable; final review will be author self-review.

## Current implementation and limits
The initial all-seams-must-match hypothesis failed official train[0]. Correct
assemblies instead have a connected graph of completely matching colored
contacts; unrelated contacts may cross genuine color boundaries. The resulting
general reference matches all four supplied labels. Python checks unique final
outputs; Racket returns the first valid assembly. The synthetic grammar is
filtered by the unique-output Python solver, so that distinction is outside the
admitted grammar, not a claim that arbitrary ambiguous inputs are defined.

Generated images use varied doubled-cell color textures, 4/6/9 fragments,
rectangular and L-shaped fragments, all global D4 poses, varied palettes and
sizes. This is a complementary sampler subset, not the full parent distribution;
it does not emulate every long multi-loop texture in the originals. The marker
must be the unique three-cell color forming an L, and background is the modal
input color. All original inputs satisfy these constraints. First-demo rejection
sampling defeats the declared largest-region shortcuts; finite rivals do not
prove universal learnability.

A protected 30x30 seed-43 query initially exceeded the unchanged 10-second Racket
limit. Pairwise seam compatibility is now cached and coordinate contact lookup
uses hashes. The original timeout regression and seed-17 stress both execute.
The standalone ordinary generator is built from core.py; run build_generator.py
--check to detect drift. The adapter imports only adjacent source/resources.

Final self-review: returned private profile dictionaries are deep-copied from
the cached scene bank. An isolation regression proves mutating a returned episode
cannot poison subsequent metadata. Final source-bound receipts are regenerated
after this repair; the earlier inventory is not acceptance evidence.
