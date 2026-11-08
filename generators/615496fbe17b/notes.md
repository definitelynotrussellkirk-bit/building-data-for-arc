# Working notes: 615496fbe17b

## Review decision

The original generator was not ready for native admission: unknown controls were silently accepted, the self-check could accept an unsealed large hole, and object placement could silently omit a distractor. The production sampler is now version 2.2.0 with strict controls, complete-scene retry packing, exact override validation, a pure canonical rule mirror, and a semantic uniqueness check for the hole-sealing object.

The native family is `hole_behavior={sealed,persistent}`. `sealed` preserves the canonical default byte-for-byte. `persistent` selects the unique object whose enclosed hole remains after one clipped 3×3 dilation. Inputs are matched across settings, prefix-stable for 2–6 demonstrations and 1–4 queries, and include substantive 30×30 scenes.

A bounded audit over 32 seeds found no surviving declared rival, packing failure, label mismatch, or projection defect. The exact seed-19/profile-5 placement failure found during development is retained as a regression. The causal witness substitutes the other setting's selected-object intermediate and changes the protected-Racket output.

## Next owner action

Review and integrate the exact source delta, rerun native qualification on the integrated source, then perform semantic acceptance. Training admission remains separate. The finite rival bank is evidence against the tested shortcuts, not a proof of universal uniqueness.
