# 26e0ef7cf48b

A black grid contains one connected red (2) template, green (3) and yellow (4) one-cell anchors, and optional maroon (9) walls. Normalize the template to its bounding-box top-left and stamp that same shape in cyan (8) at every 3/4 anchor. Discard stamped cells that are outside the grid or lie on a 9. Overlapping copies merge. Sequential lessons cycle through wall blocking, boundary clipping, overlap, and an uncluttered base case so the query rule is demonstrated rather than hidden.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
