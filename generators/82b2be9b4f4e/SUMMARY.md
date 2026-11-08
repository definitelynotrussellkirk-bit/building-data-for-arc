# 82b2be9b4f4e

A bottom-left nonzero key selects the largest of one or two isolated objects of
that color. Clear the key cell, crop the selected object's bounding box, and
upscale the crop by 2 on both axes. Two or three independently colored
single-component distractors vary the scene.

Reviewed generator version: `3.0.0`. The sampler has five exact, observable
axes (`grid_h`, `grid_w`, `key_color`, `n_key_blobs`, `n_distractors`) and a
four-slot `canonical, discriminator, broad, discriminator` schedule. The two
discriminator slots make every three-demo subset of a four-pair window refute
the canonical-fitting shortcut “crop all pixels of the key color,” including
all cyclic choices of which pair becomes the query.

Kind: `per_puzzle`. Canonical rule pin: `eff131529ace`. Approval remains a
catalog/maintainer decision; this review does not alter training admission.
