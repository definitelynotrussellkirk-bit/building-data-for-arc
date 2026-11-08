# Root-cause analysis

The imported sampler is not merely missing validation metadata. It changed the
answer-bearing domain: canonical frames contain **two** candidate templates
(colors 1 and 2), and the bottom selector cell chooses one. The baseline draws
only the already-selected template, often in colors 3–6, so a solver never has
to learn local candidate selection. The baseline also advertises controls it
does not honor, accepts unknown controls, omits `RULE_HASH` and `self_check`,
produces zero canonical size/palette profiles, and has no executable semantic
counterexamples.

Repair hypothesis: restoring the canonical two-candidate frame grammar, using a
small pixel-observable override surface, and scheduling counterexamples to
selection-, transform-, ordering-, and alignment-shortcut rules will make the
new regression suite fail on the baseline and pass without changing the Racket
authority.
