# d48317a7c7c8

On a background-0 grid, find monochrome 4-connected components of exactly three yellow (4) cells that form a straight horizontal or vertical bar. For each end independently, paint cyan (8) one step beyond it if that position is in bounds and was background in the original input. Preserve yellow cells, occupied caps, other colors, longer bars, and bent components. Diagonal contact does not merge components; shared available caps may be painted once.

Version `3.0.0` generates varied contrasting scenes: valid targets, wrong-color three-bars, overlong and bent yellow foils, diagonal contacts, clipped endpoints, and occupied endpoints. Ordinary draws contain at least two targets. Exact controls are height/width 8..24, target count 1..10, and a nonyellow distractor color; feasible joint packing and the explicit one-target control are documented in `notes.md`. Three demonstrations are the declared lesson minimum, with executable rival and rotation checks retained in the review evidence.

Kind: `per_puzzle`. Canonical rule hash: `b2af6531f18d` (unchanged).
Approval is derived by the catalog from current code and retained evidence.

A proposed native parametric adapter in `workspace/parametric/` also supports an
episode-fixed exact target length of 3 (canonical) or 4, with independent 2–6
demonstrations and up to four queries. Retained public episodes use exact
canonical bytes and `challenge-<full-sha256>.json` visible identities; the current
manifest is `a71357e5a75e79dfb686b9506a4768ce53c63cc28d554aa9f960cfb1977cb072`.
It has bounded Racket-backed evidence and fresh qualification, but is not accepted
or admitted to training.
