# 5ccdbe078da6

Version `3.0.0`; canonical rule pin `d8da2d7cc24b` unchanged.

Zero-background ARC grids contain one to three distinct foreground colors, each
appearing at two distinct cells. Each pair defines an axis-aligned bounding box;
the output paints its border, including horizontal/vertical line cases. Colors
are painted in row-major first-occurrence order. Later borders overwrite earlier
ones, including original markers: marker preservation is not an invariant.

Public controls: height 4..10, width 5..12, pair count 1..3; palette
`default|warm|cool|varied`; pair kind
`mixed|down_right|down_left|horizontal|vertical`. Valid pins have the same domain
in every difficulty band. Unknown controls and noninteger numeric pins reject.
Default profiles mix canonical-sized two-color scenes with wider scenes.

The generator emits inputs only. Canonical Racket remains label authority.
Review mirror/rivals are diagnostics, not approval. Default three-demo lessons
are not guaranteed to identify the rule; `workspace/lesson_cover.py` builds
finite-rival-covered research lessons from verified inputs. See workspace notes.

Approval remains derived from the catalog and retained evidence; this review
makes no manual approval or train-safety change.
