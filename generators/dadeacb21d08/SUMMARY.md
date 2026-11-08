# dadeacb21d08

Complete **only** red (2), four-connected components that have exactly three cells and a 2×2 bounding box. Each qualifying L-triomino is replaced by a full green (3) 2×2 square. The fourth corner is painted green even when it was occupied by a different color. Red dominos, straight triominoes, full 2×2 squares, larger red components, non-red L-triominoes, and all unrelated cells remain unchanged.

The version 3.0.0 sampler uses a deterministic four-profile curriculum. Every linked four-example window includes exact red L targets together with red shape/count negatives, non-red L negatives, empty and occupied missing corners, all four L orientations, edge targets, and examples outside the narrow canonical size/count envelope. The declared axes are exact controls: grid height and width 10–16, 2–4 targets, 1–3 red decoys, 1–2 non-red decoys, `empty|occupied|mixed` target holes, and `interior|edge` target placement.

A task-local Python mirror, semantic witnesses, canonical-compatible shortcuts, and lesson competitors make the teaching contract executable. The retained independent probe exhausts all 192 joint boundary combinations and rotates every four-profile start through the query position.

Kind: `per_puzzle`. Selected version: `3.0.0`. Canonical rule hash: `4dc2707cc06e`.
Approval remains catalog-owned; passing review checks does not itself approve training use.
