# Current decisions: 9f362acbf729

The previous `1.1.0` implementation generated unrelated colored motifs. Version `2.0.0` now implements the canonical four-corner transform-key task and pins the normalized canonical Racket rule as `RULE_HASH = 75692873c100`; the canonical rule itself is unchanged.

The input canvas stays at the canonical 5×5 size. Variation is in tight body dimensions 2..4, one to three body colors chosen from 5..9, body placement, and all 24 corner-key permutations. Keeping larger canvases was rejected after the defect detector found that 27/60 generated pairs shrank while the canonical training pairs grow.

Key semantics are exact: 1 = clockwise quarter-turn, 2 = half-turn, 3 = left-right flip, 4 = transpose. Each pair of transformed shapes is top-aligned with one zero column between them; the two galleries are right-padded to equal width and separated by one all-zero row.

Generated bodies normally expose four distinct keyed images. The sole three-image exception is the canonical 2×2 monochrome L profile, where two canonical transforms coincide. The sampler and self-check both encode that exception narrowly; other three-image bodies are rejected.

`numeric_rotation` is retained as an executable semantic rival (incorrectly treating keys as quarter-turn counts). Every generated scene is required to disagree with it, and `WITNESS_RIVALS` binds that claim for the semantic gate. The 24-value `key_order` axis is marked diagnostic only to avoid the generic 16-value probe cap; task tests explicitly force and observe every permutation.

Current evidence covers canonical-pair parity, staged Racket rule smoke, override behavior, sampler boundaries, malformed-input rejection, transformation drift, profile support, and semantic-rival disagreement. The Python mirror is supporting evidence only; the canonical Racket program remains output authority. No full all-stage battery was needed for this repair, and packaging does not itself grant approval or training admission.
