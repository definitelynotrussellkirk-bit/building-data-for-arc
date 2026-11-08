# Working notes: 138ffc14ac65

The retained base exposed global ranges that crashed inside difficulty-specific draw bounds and advertised metadata-only axes. Version 2.0.2 narrows the public contract to four operational axes, honors every numeric value across all difficulty bands, makes helpful textures behaviorally real, and adds the missing canonical `RULE_HASH`.

The native parametric family adds `finish_rule=equal_top_bridge`: canonical upward projection is Stage A; Stage B reads the newly derived top-edge endpoints and bridges colors occurring exactly twice. Inputs contain no top-edge seeds, so a Stage-B-on-raw-input ablation cannot recover the output.

- Ordinary generation now requires 2..8 seeds; the unsupported one-seed endpoint is rejected instead of passing as a generic singleton impostor.

- Final lint, self-check, rule-smoke, and defect-lint stages pass; scalar call arguments fail closed and the ordinary grammar rejects unsupported singleton lessons.
