# Public parent 1818057f: simultaneous plus detection and component selection

## Canonical rule
Find all five-cell orthogonal crosses whose center and four neighbors are color 4. Paint the union of those five-cell stencils color 8. Diagonal neighbors may be occupied and arms may extend farther; detection is simultaneous on the original input, so overlapping crosses are not suppressed by earlier recoloring. Every other input cell is preserved. This general rule matches all three supplied demonstrations and the supplied test gold through protected Racket. It is also defined for empty-cross, one-cell, thin, and boundary-touching scenes.

## Settings and sequential dependency
`selection=all` is byte-identical to `reference.rkt`. `selection=largest` first finds the crosses and four-connected color-4 components, discards components without any cross, selects the largest remaining component by occupied-cell count (row-major first-cell tie-break), and paints only crosses with centers in that selected component. The selected component and its center list are the input-dependent intermediate consumed by the final stencil renderer. A larger unrelated component must not suppress the actual winning cross-bearing component. The smallest-bearing-component counterfactual changes 25 output cells on the exact preflight stress query.

The generated noncanonical extension uses explicit four-connectivity. This is a declared variant, not an assertion that the original labels imply global component selection.

## Generation and teaching
2–6 demos and 1–4 source queries are independently prefix-stable, matched across settings and copy-isolated. A two-demo teaching bank includes embedded crosses, overlapping crosses, a large no-cross frame, a sparse large-bbox distractor, and diagonally touching distinct components. The largest component changes motif between the two demonstrations, preventing a fixed-template interpretation. D4 presentation and spatial assignments vary by seed. A bounded 256-attempt teaching search refutes the 18 named rivals for both settings without inspecting queries.

Extra demos and all queries grow random connected appendages in the motifs, creating new sizes, cross counts and overlapping stencils rather than replaying only a small fixed template menu. Non-target background colors vary, consistent with a color-4-specific rule; the output cyan role remains fixed. Frames are optional outside teaching/stress scenes. The 30×30 stress query has boundary-spanning color-4 content and over 100 foreground cells. Query presentation independently shuffles the complete four-query bank before taking a prefix. One public file contains only demonstrations and one unlabeled query; future inputs, answers, setting, program, seed, order and total count remain controller-private.

## Actual verification
33 task-local tests passed, including original labels via protected Racket, boundary/no-cross/overlap literals, malformed control/grid rejection, relocation of only declared native resources, and a query-size/palette diversity regression. Preflight passed 4 jobs (two settings × seeds 17/43). The source-bound audit covered 64 episodes, 640 visible source pairs, 1,152 named-rival lesson checks, 576 independent count-prefix checks, 64 30×30 cases, 40 protected label evaluations, 108 executable-rival evaluations, and a separately replayed causal witness. Eight ordinary canonical generated cases also passed protected Racket parity.

No query-changing survivor among the declared finite rivals was found. This is not universal identifiability or evidence of measured model-training benefit. The full unmodified shared repository suite was not rerun; verification is scoped to both assigned task suites, reused helper tests, and native authoring checks. Catalog task-tests returned Unknown puzzle because owner registration is still pending; the complete direct task-local suite passed.

## Owner handoff
Register exact source/provenance and the faithful original reference, review it, and run unchanged native qualification plus fresh acceptance separately. No shared catalog, canonical data, approval or runtime was changed. Neither acceptance nor training admission was performed.

## Current repeated-parent reconciliation

Preserve exact all/largest-component-area programs; add exact dominant-component-plus-count and largest-overlap-cluster programs, all three constructors. Demonstration-only known-rival coverage requires three demos (3..6 supported); query constructor cycles by seed. Standalone ordinary generator flattens the unchanged current sampler; replayed baseline inputs are identical. Generator-file-only copying is a stronger portability probe; the prior declared-closure runtime was already accepted. Current evidence resides in evidence/repeat-third-union. Private native acceptance and root publication are separate.
