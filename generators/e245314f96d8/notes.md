# Working notes: e245314f96d8

## Review decision

The retained template-memorizer finding was reproduced: the old `all_degrees` sampler yielded only one D4-normalized occupancy mask. The production generator is now version 3.1.0 and builds degree-2/3/4 contact graphs from three non-isomorphic internal spines, then grows lawful random morphologies while preserving the canonical contact graph. A regression gate requires all three topologies and at least 48 D4-normalized masks; the repaired sampler produced 192 in the bounded audit.

The native family is `contact_neighborhood={cardinal,king}`. `cardinal` preserves the canonical default byte-for-byte. Both settings first segment same-color four-connected objects, then differ only in the contact graph used to compute degrees before applying the canonical 0→3, 1→4, 2→6, 3+→8 repaint map. Inputs are matched, prefix-stable for 2–6 demonstrations and 1–4 queries, and include a substantive 30×30 scene with 100 objects.

The two-example curriculum constructively separates cardinal from king contact and the declared rival bank. A bounded audit over 32 parametric seeds plus 64 production seeds per difficulty band found no label, teaching, projection, topology, or stress failure. The causal witness substitutes cardinal degrees into a king episode and changes the protected-Racket output.

## Next owner action

Review and integrate the exact source delta, rerun native qualification on the integrated source, then perform semantic acceptance. Training admission remains separate. The finite seed/rival audit does not establish uniqueness against every possible ARC program.
