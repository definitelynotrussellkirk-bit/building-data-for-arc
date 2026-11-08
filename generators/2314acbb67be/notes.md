# Working notes: 2314acbb67be

## Review e9d552543e859448: base repair and native motif-order family

### Base review and repair

The catalog-selected canonical rule is coherent: discover monochrome nonzero
objects, crop them, sort by descending occupied-cell count with deterministic
source-position/color tie-breaks, and pack the crops horizontally with one zero
column between them. Its Racket source and stored original labels were retained
unchanged.

The inherited Python generator advertised controls that did not determine its
output reliably (`palette_size`, position/texture-style controls) and did not
provide a dependable source for a two-key ordering lesson. I replaced those
claims with four exact observable axes: `grid_h`, `grid_w`, `n`, and
`palette_kind`. Unknown keys, booleans/nonintegers, out-of-range dimensions, and
geometrically impossible requests fail explicitly. Generated motifs have unique
colors, distinct occupied-cell counts, separated component halos, and lawful
packing geometry. The repaired generator SHA-256 is
`3dc04f72f9af1756cc7bd1ae47e271176ab0c2c929cb75bf8f2f7a16c81504a3`.

### Parametric design

The native family fixes one episode-level `order_key`:

- `cell_count`: exact byte-for-byte canonical program.
- `bounding_box_area`: discover and crop the same motifs, rank them by descending
  crop area with the same tie-breaks, then use the unchanged horizontal packer.

This is a real A → intermediate → B dependency. Step A produces an input-derived
ordered list of motif crops and measurements; Step B cannot pack the gallery
until that order exists. A protected counterfactual substitutes canonical
cell-count ordering for area ordering and changes the final grid while keeping
the packing operation unchanged.

The family supports 2–6 demonstrations and 1–4 queries with deterministic,
matched, prefix-stable inputs. Every supported demonstration distinguishes the
two settings. The four-query schedule is 10x14, 16x20, 24x27, and 30x30; the
stress input has at least 50 motif cells and a wide nontrivial output. The finite
self-audit probes left-to-right, color, ascending-score, width, perimeter, and
no-gap shortcuts on seeds 0, 17, and 97 for both settings; all six reports have
zero query-changing survivors.

Protected Racket authoring preflight passed all four jobs and 32 labels, including
ordinary base draws and original-pair replay. Twenty-three task tests pass.
Sixteen one-query public projections pass source verification, 24 private-field
invariance checks, and four visible-change controls. These finite checks do not
prove universal uniqueness. Owner exact-source review, fresh native
qualification/acceptance after integration, and training admission remain
external and unclaimed.
