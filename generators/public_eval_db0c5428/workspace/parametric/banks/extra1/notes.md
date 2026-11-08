# public_eval_db0c5428 — missing-center tile projection family

The official source is a 3×3 array of equal square tiles embedded in a modal
background. Its center tile is blank. The canonical rule reconstructs that
missing tile from the inward-facing boundary of all eight neighbors: corner
neighbors supply corners, edge neighbors supply the corresponding edge, and the
interior uses the common base color. It retains the reconstructed 3×3 array and
copies each surrounding tile two macro-steps through the center, producing a
centered 5×5 macro layout on the original canvas.

The implementation is general over odd tile sizes 3 and 5 and matches every
supplied training and test label. It infers the modal background, source bounding
box, tile size, base color, inward samples, output origin, and center tile from
the input rather than storing supplied grids.

The native family adds `outer_scope=all|modal_inward`:

- `all` is the byte-exact canonical rule.
- `modal_inward` reconstructs the same center and retains the same inner 3×3
  array, but emits an outward copy only for tiles whose inward anchor has the
  uniquely modal sample color.

Generated lessons vary tile size, canvas placement, palette, tile decoration,
modal sample identity, and which five of the eight positions carry it. The first
two demonstrations reverse first/last membership and numeric color ordering,
defeating the retained position, corner/cardinal, numeric-color, rarity, and
fixed-prefix shortcuts. Four private queries culminate in a dense 30×30 case.

The sequential dependency is substantive: Stage A reconstructs the missing
center and measures the eight input-dependent inward samples; Stage B cannot
select outward copies under `modal_inward` until their multiplicities are known.
The retained counterfactual replaces the computed modal sample with a known
nonmodal record and changes the protected-Racket output.

This is reviewer authoring evidence only. Owner source review, registration,
native qualification, acceptance, and any training admission remain pending.
