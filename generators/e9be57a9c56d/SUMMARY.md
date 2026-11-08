# e9be57a9c56d

The uniquely largest 8-connected object is a template. Singleton markers lie on one row or one column; exactly one marker shares the template color and anchors a chain. The selected rule stamps a recolored template for every non-anchor marker, with consecutive marker gaps determining edge-to-edge copy spacing.

Kind: `per_puzzle`. Generator version: `3.0.0`. Declared minimum demonstrations: `3`.

The exact public axes are `orientation`, `n_markers`, `template_size`, and `anchor_pos`; each is observable from the returned grid. The default four-draw schedule covers all canonical `(height, width, palette_size)` profiles and includes both non-color-2 anchors and interior anchors so the canonical fixed-color and endpoint shortcuts are explicitly taught against.

The canonical Racket rule remains authoritative (`RULE_HASH = f8100feef807`). Approval is derived by the catalog from current code and retained evidence; this review does not mark the generator approved or training-safe.
