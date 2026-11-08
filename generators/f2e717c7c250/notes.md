# Working notes: f2e717c7c250

- Repaired the inherited `n_keys` contract: the canonical program uses exactly two header keys, so the generator now declares and strictly consumes only `n_keys=2`, rejects unknown/coerced overrides, pins `RULE_HASH`, and supplies a semantic `self_check`.
- Native parametric design: `crop_only` (byte-exact canonical default) and `dominant_key_rotate`. The alternative first constructs the canonical crop, then rotates that crop according to which header-ordered key contributes more cells inside it.
- Teaching: demonstration 0 makes key 0 dominant; demonstration 1 makes key 1 dominant. Both use asymmetric crops and distractors. Additional examples vary dimensions, colors, positions, and density; query 3 is 30×30.
- Causal ablation: swap the dominant-direction intermediate so clockwise/counterclockwise are reversed. The protected Racket witness must change the final output.
- Finite self-audit is not a uniqueness proof. Owner source review, native qualification/acceptance, and training admission remain separate.
