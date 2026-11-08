# Working notes: 3a6ce35e3549

## Current parametric build

The native family preserves the canonical `blob` behavior byte-for-byte as the default and adds an episode-fixed `gaps` setting. In both settings, the input-dependent first step identifies the four minority-color corner markers and derives their strict interior crop. The second step selects either the majority-color blob cells or the complementary gaps inside that crop, then recolors the selected cells with the marker color.

The adapter supports every 2–6 demonstration prefix and exactly four queries. The bounded self-review exercised 32 seeds, 64 episodes, 640 labeled pairs, five semantic rivals, varying marker bounds/output shapes, and substantive 30×30 cases. Focused tests and staged task tests passed. The source-bound authoring preflight replayed both settings at seeds 0 and 17 through protected Racket (40 evaluations), and the causal witness shows that shifting the inferred crop bounds changes a valid output. The public projection produced 16 one-query views; first-turn invariance and positive controls passed.

Exact canonical source was not changed. The family is a reviewer-ready prototype only: finite rivals/seeds do not prove universal identifiability, and owner source review, native qualification, acceptance, and any training admission remain pending.
