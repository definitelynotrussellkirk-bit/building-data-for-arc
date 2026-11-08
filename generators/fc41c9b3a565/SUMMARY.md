# fc41c9b3a565

Treat each nonzero monochrome 4-connected component as an object. Normalize the
object to its own bounding box. Keep its original cells and color exactly when
the normalized mask is invariant under a 180-degree rotation; erase every other
object to background 0.

The v4.0.0 curriculum combines exact linked canonical morphology anchors with
broader counterexamples. Ordinary scenes contain a point-symmetric-only kept
object and matched-size/bounding-box erased decoys, so left/right reflection,
up/down reflection, size, aspect, position, and canonical-prototype shortcuts
cannot explain the labels. Every object has a distinct nonzero color and objects
remain separate 4-connected components.

Declared exact axes: grid height 6–10, grid width 6–10, and one of four semantic
role-count profiles. Four demonstrations are required per generated lesson.

Kind: `per_puzzle`. Generator version: `4.0.0`. Canonical rule hash:
`735d17bb2ca5`. Approval remains catalog-derived from current code and retained
evidence.
