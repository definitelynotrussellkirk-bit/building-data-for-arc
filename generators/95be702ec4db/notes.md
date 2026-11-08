# Working notes: 95be702ec4db

- Repaired the inherited validator/control surface. The previous `self_check` rejected canonical 22-column examples and assumed only 5×5 frames; the current validator recognizes the canonical mixed 5×5/6×6 gallery, checks exact borders, one connected single-color interior shape, and 3–5 frames. `grid_w` and `n_frames` are strict observable controls; ignored advertised axes were removed; `RULE_HASH` is pinned.
- Native parametric design: `full_matrix` (byte-exact canonical default) and `selector_row`. A top-row one-based selector chooses a row only after the complete rotational-equivalence matrix is constructed.
- Teaching: the first two demonstrations select different rows in different partitions. Additional examples vary frame count, partition, positions, shape rotations, colors, and selector; query 3 is a 30×30 diagonal gallery.
- Causal ablation: replace the selected row index with the next row. A protected Racket witness must change the final relation vector.
- Finite self-audit is not a uniqueness proof. Owner source review, native qualification/acceptance, and training admission remain separate.
