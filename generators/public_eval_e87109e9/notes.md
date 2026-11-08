# public_eval_e87109e9

Current authoring decision: the top six rows are a color-to-left/right legend.
The color-8 square emits four rays of its own width; a ray turns immediately
before each colored obstacle according to the legend, and all traversed
background cells become color 8 after the legend is removed.

The native variant `turn_policy=opposite` reverses every decoded turn while
retaining the same seed, obstacles, and collision detection. Generated lessons
include a ray that encounters a second obstacle after its first turn, so the
rule cannot collapse to four independent straight segments. Four private
queries are seed-shuffled; the largest input and output stress lawful 30-column
geometry with a 30x30 input and 24x30 output.

The bounded adversarial pass exposed one seed where alternating legend
positions accidentally encoded the left/right commands. The two minimum
demonstrations now place both left-turn entries consecutively and both
right-turn entries consecutively (with within-pair order still seed-varying),
so a legend-position-parity shortcut is directly contradicted while every
obstacle color remains exercised by the four source rays.

Owner registration under `ee_e87109e9`, native qualification, source acceptance,
and any training admission remain pending.

## Current repeated-return reconciliation

Excluded conflicting header-command route grammar: preserved current collision rays disagree on 9/20 incoming default examples. Exact counterexamples retained; no semantic equivalence claimed. Excluded conflicting target-approach/bounce grammar: preserved current collision rays disagree on 15/20 incoming default examples. Exact counterexamples retained. Partial sampler contribution: canonical-consistent route scenes enter the setting-independent bank. shortest-route highlight semantics remain unmerged because its solid-rectangle obstacle parser rejects incumbent shapes. Not fully incorporated. Exact incumbent legend/opposite programs and current chained-collision sampler retained.

All original accepted programs and defaults remain exact. Two to six demonstrations and four shuffled, sequential private queries are supported. Finite rival checks and sampled protected labels are bounded evidence. Fresh private native qualification and acceptance re-execution passed. Live publication and training admission remain separate. Source-bound decisions and witnesses: `evidence/reconcile-18/`.
