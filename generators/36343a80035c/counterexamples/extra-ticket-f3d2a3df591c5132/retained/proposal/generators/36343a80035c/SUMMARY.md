# 36343a80035c

Treat all nonzero input cells as walls. On a fresh zero grid, paint 8 on exactly
the 4-connected zero regions that do not touch the border. Different colors and
separate wall components may cooperate to enclose a region.

Kind: `per_puzzle`. Proposed candidate version: `3.1.1`.

The four-profile sampler includes canonical-scale anchors, nonrectangular L/T/S
holes, diagonal-contact counterexamples, cooperative cages, cyan wall distractors,
and open-U decoys. Every draw now also contains a border-connected zero region
of area at most four, teaching that small size alone does not imply enclosure.
The conditional two-wall corner construction preserves existing hole regions.

Profile names preserve their historical area signatures. Ordinary draws still
have two holes of area at most four and 9..14 dimensions. This remains a finite
construction family. The reference rule is unchanged. This source is a tested
reviewer proposal; owner integration and exact-source acceptance are pending.
