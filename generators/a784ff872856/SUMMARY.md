# a784ff872856

Extract every nonzero same-color 4-connected object, crop it to its bounding box, sort by bounding-box width descending, then height descending, then color ascending, and vertically pack the left-aligned crops with one zero row between neighbors.

Every ordinary draw retains the primary width-vs-cell-count inversion. Three-object draws alternate equal-width/different-height and equal-dimension/different-color lessons; four-object draws contain both. The four-step schedule therefore teaches all three keys of the pinned ordering rather than only its primary key.

Kind: `per_puzzle`. Generator version: `2.1.0`. Generator SHA-256: `6790a56640ea1cf49ca945e6794781b42dedcda4dc1c8eb72e0cc1c9b2e8a064`. Racket rule hash: `7991026f57da`.
