# Current review decisions

- General rule: choose the row/column axis containing strictly more same-color pairs. Each selected pair defines an arithmetic progression by its input-derived spacing.
- Canonical `marker_policy=resolve`: a unique differently colored cell on that progression supplies the final color and bounds the completed span; without one, the pair color extends to both canvas boundaries.
- Alternate `marker_policy=pair_extends`: retain the derived axis/period records but ignore marker resolution and extend the pair color through the full in-bounds progression.
- The first two generated demonstrations cover both orientations, marker-resolved and marker-free signals, non-unit periods, unrelated singletons, and bounded-vs-full extents.
- Sequential chain: A derives the global axis and per-line period/marker records; B consumes those records to choose the painted coordinates and colors. The retained counterfactual selects the minority axis.
- Finite rivals are bounded executable checks, not a universal uniqueness claim. Owner registration, exact-source review, qualification, acceptance, and training admission remain pending.
