# public_eval_65b59efc — template-blueprint expansion family

The official rule is reconstructed from all supplied demonstrations and test
gold. The upper band contains three or four monochrome square templates. The
middle band contains separated placement panels that overlay into one
color-coded blueprint. Detached lower singletons map each template color to its
output color. Every blueprint cell is expanded into the corresponding template
mask and recolored from that legend.

The native family adds `placement_scope=all|modal_template`:

- `all` is the byte-exact canonical rule.
- `modal_template` first overlays the placement panels, counts the requested
  template colors, selects the unique modal template, and expands only its
  blueprint cells.

Inputs are matched across settings. The minimum lesson varies template mask
area, numeric color, panel location, placement-panel location, first placement,
and modal identity, refuting the retained finite shortcuts. The adapter supports
2–6 demonstrations and 1–4 queries. Its four private query surfaces culminate
in a 30×30 input and a 25×25 output. Public presentation reveals one query input
at a time and is independent of the private query order.

The sequential dependency is substantive: Stage A must overlay separated
panels and compare input-dependent placement counts; Stage B cannot know which
spatial blocks survive until that modal template is known. The retained
counterfactual replaces the computed modal record with the first template
record and changes the protected-Racket output.

This is reviewer authoring evidence only. Owner source review, registration,
native qualification, acceptance, and any training admission remain separate
and pending.
