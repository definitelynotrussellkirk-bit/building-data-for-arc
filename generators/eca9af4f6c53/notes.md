# Working notes: eca9af4f6c53

## Base repair

The retained audit was reproducible: `n_blocks`, `palette_size`, and `n_distinct_colors` were ignored or mutually misaligned. The repaired generator treats them as aliases for the canonical global color count, requires supplied aliases to agree, validates overrides strictly, and constructs isolated color-specific L-trominoes whose ordinary labels remain canonical.

## Native family

The default `completion_mode=global_color` is byte-for-byte canonical. The alternative `two_pass_local` applies one simultaneous local 2x2 completion pass, then recomputes eligibility on that input-dependent intermediate and applies exactly one second pass. Generated chains require the second pass while retaining a third-pass opportunity, separating one-pass, exact-two-pass, and closure rules. Episodes support 2–6 demonstrations and exactly four distinct queries; the fourth query is a substantive 30x30 case.

## Self-review and evidence

A bounded 24-job audit covered four seeds, demo counts 2/3/6, both settings, and four plausible rivals. No rival or wrong setting survived any demonstration set. A self-review found and repaired partial 5x6 slot enumeration at right/bottom boundaries before qualification. Official staged tests, protected-Racket authoring preflight, causal counterfactual replay, public projection verification, and first-turn privacy checks all passed. Owner source review, native qualification, acceptance, and training admission remain separate downstream gates.
