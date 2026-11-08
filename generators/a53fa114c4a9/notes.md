# Working notes: a53fa114c4a9

## Current decision

Version `2.1.2` reconciles the declared `n_pairs` axis with the generator's actual capacity: supported overrides are now 2–4, and hard sampling draws 3–4 rather than advertising or drawing a fifth pair that was later capped. The canonical transformation and shared authority are unchanged.

The native parametric family uses matched inputs with `column_mode = explicit_mask | merged_component`; `explicit_mask` is the exact canonical default. The alternative first applies the legend so two checkerboard source colors merge into one large monochromatic component, then retains only marked columns intersecting that recolored winner. A smaller solid decoy wins when step A is skipped, so the protected `skip_a` witness changes the final crop rather than merely changing metadata.

The sampler includes 2–6 demonstrations, four sequentially projected queries, ties the setting to visible demonstrations, and includes a boundary-spanning 30x30 case. Reviewer checks are finite rather than universal: 42 focused tests, 96 protected Racket audit evaluations, 64 audit seeds, the cross-family 512-seed fuzz pass, public projection/privacy checks, and the protected causal replay. Next useful action is owner-side native qualification and fresh acceptance against these exact source hashes. No variant approval, owner acceptance, or training admission is claimed.
