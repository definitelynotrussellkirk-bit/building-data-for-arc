# Current authoring decision

The original is an eight-tile ring on cyan, with a missing central tile. Each
outer tile is reflected across its outward-facing row/column axes and placed
one tile farther out. Central positions sample the inward-facing pixels of the
corresponding directional tile; the center retains the ring's modal base color.
All supplied tiles are 3x3. The input is preserved; out-of-canvas copies clip.

Implement `extension_policy=all_tiles|largest_port_run`. The default reproduces
all four supplied labels. The alternative reconstructs the central directional
key, finds its largest four-connected same-color nonbase run, and reflects only
those outer tiles addressed by that run. Disconnected same-color ports do not
combine. No answer tables or original data are read by generation.

Plan: tests of original labels and a literal asymmetric eight-port ring first;
then independent Racket and Python rules, setting-neutral constructive lessons,
2..6 demos and 1..4 privately shuffled query prefixes, one four-ring 30x30 case;
then executable rival attack, protected preflight and source-bound witness.
Public originals contain one ring; multiple separated rings and clipped copies
are explicitly generated extensions, not claimed additional official evidence.
Native grammar uses complete noncyan 3x3 tiles with a modal base and a unique
largest nonbase port run. No overlapping projected rings are admitted.

Implemented: independent Python and Racket references reproduce all four official
labels. Current 26 tests pass. The 20-seed audit passes 800 requests, 5,200 pair
instances, 200 distinct inputs, 400 matched-setting comparisons, 2,000 public
turns and 156 protected Racket applications, including every declared rival.

Self-review found a real shortcut: second-most-frequent center color agreed with
both old demos and disagreed with all four retained queries (12 protected labels).
Repaired the 3/2 run-length lessons to 2/4. A naive first revision then exposed
orientations where eight-connectivity still survived; the first lesson now must
explicitly distinguish diagonal joins. The retained regression catches the
original shortcut and the repaired bank passes. A separate 24-evaluation replay
checks exact historical grids/programs and the repaired lessons at seeds 0,17,43.
An initial unmatched final Racket delimiter was caught before any labels were
trusted. No original data/provenance was edited. Review was an author self-review;
finite seed/rival checks do not prove universal identifiability or learning gain.
