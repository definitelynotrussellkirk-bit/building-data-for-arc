# Wire-selected color transfer

Goal: infer and execute all six original labels, preserve canonical one-hop transfer, and provide a native follow-chain alternative.

Approach: recover colored beads, suppress redundant gray diagonal edges, identify the two endpoint-aligned beads by a unique distinct assignment, then resolve their input-defined color pointers. The canonical transfers one donor center; follow-chain resolves until a terminal or repeated color. The alternate exposes variable-length input-dependent lookup, not an output-only color remap.

Implementation sequence:
- [x] Failing original-label, endpoint, count, privacy and strict-type tests.
- [x] Pure Python parser/constructor, protected Racket rule, portable native adapter and ordinary generator with drift builder.
- [x] Bounded shortcut self-review, repair discovered teaching holes, strict public exports and causal counterfactual.
- [x] Protected authoring preflight and isolated-resource checks.

Review focus: endpoint ambiguity, 8-neighbor corner cutting, clipped beads, coincident center/body colors, cyclic pointers, private bank leakage, shared mutable data.

Constraints: only this task home; original parent immutable; no catalog or acceptance edits. Supplied and generated labels must execute through protected Racket. Source-driven self-review only; no independent reviewer available.

Final review: author self-review (no subagent tool). Scope-limited external
acceptance is pending; the uploaded original remains immutable.
