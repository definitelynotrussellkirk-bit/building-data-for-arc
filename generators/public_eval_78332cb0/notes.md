# Current authored border-contact family

Canonical: split equal-sized panels at complete magenta (6) divider bands.
Orange (7), not black, is background. Match nonempty foreground contact sets
across opposite panel borders, ignoring foreground colors. The unique open
head-to-tail chain determines order AND horizontal/vertical output orientation.
Preserve panel pixels and divider thickness; do not rotate or mirror tiles.
All five supplied labels match under protected Racket, including the same-color
example, opposite input/output layouts and distinct shapes of identical area.

Alternative `counting=prefix_parity`: after reconstructing the chain, accumulate
foreground cell counts in that order. Recolor a panel's foreground to cyan (8)
exactly when its cumulative count is odd. This is not own-area or rank parity.
The protected wrong-intermediate witness leaves the assembly geometry correct
but assigns cumulative counts using the scrambled input order.

Grammar: 2..6 nonempty equal-size panels; uniform-width full dividers, no outer
divider frame or magenta inside panels; a UNIQUE open chain; legal 1..30 output.
The sampler emits 2..5 panels, varied connected branching shapes, singleton and
multi-cell contacts, both chain axes and row/column/matrix input layouts. Black
foreground is supported. Query profiles include same-color and repeated-color
panels plus a substantive 30x30 scene with two-cell divider bands. Whole-set
multiport equality, rectangular panels and thick bands are authored extensions
not uniquely forced by the original singleton-contact examples.

Teaching repair: seed 48 previously made ascending color order fit both minimum
demonstrations and fail a query. First-demo colors are now deliberately
non-monotone along the recovered chain. The original bad lesson is retained in
tests/color-shortcut-before.json. `replay_color_shortcut.py` executes the correct
and color-sorted Racket programs on that lesson and the repaired demos, without
changing the canonical rule. Another regression requires exact full contact sets
rather than a single overlapping port. Ambiguous chains are rejected explicitly.

Independent 2..6-demo/1..4-query requests use a full privately shuffled four-query
bank before truncation, matched inputs between settings, isolated local RNGs and
fresh mutable metadata. Native closure is adjacent adapter/engine/canonical;
ordinary generator.py is self-contained and reproduced by build_generator.py.
Audits include input/reversed/area/color order, partial-contact routes, forced
axes, own/rank/raw-input/color-count/bounding-area/reversed prefix counts and
corresponding alternate-setting order faults. Finite checks are not a uniqueness
proof or evidence of training benefit. Owner registration, semantic review,
qualification, acceptance and training admission remain pending.

Owner worker API correction: use the existing worker input/findings contract. Earlier author checks used the incompatible return convention. Reference programs are unchanged; owner preflight and native acceptance determine current readiness. See evidence/owner-base-api-repair.json.

## Current repeated-return reconciliation

Preserve exact canonical/prefix-parity programs. Port reverse-and-rotate assembled chains and color-9 central-panel highlighting onto the incumbent contact-chain parser. Center highlighting applies to odd chains; even chains retain canonical rendering. Compatible incoming constructors remain; nonuniform separator bands, unsupported panel counts and other rejected grammars are explicit exclusions. The 68468 constructor is excluded entirely from executable banks; its reverse semantics are already supplied by 98c8. Two visible lessons separate finite order/count/center rivals. Evidence: `evidence/reconcile-15/`. Private native qualification, fresh native acceptance re-execution and bounded protected execution passed. Live publication and training admission remain separate.
