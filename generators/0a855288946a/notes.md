# Working notes: 0a855288946a

## Review-a6774a1d00d02ab4

- **Base review:** generator `3.0.0` was retained unchanged. Its ordinary sampler and exact canonical whole-grid 180-degree rule were already sound; only the legacy test was made relocation-safe by resolving the packaged source root rather than a machine-specific path.
- **Canonical preservation:** `rotation_scope=all_cells` uses the byte-exact canonical Racket program, SHA-256 `d4b6baaa86e77b4933796b2dfcb7d5d4e37d9b267fa0d37bbe84839cc0d1e257`.
- **Native family:** added `rotation_scope=rarest_color_orbits`. Step A counts nonzero colors, chooses the unique least-frequent color, and records its coordinates. Step B swaps exactly the 180-degree orbits touched by that coordinate set.
- **Teaching repair:** the first bounded audit found a numeric-color-rank shortcut in the early sampler. The retained sampler now gives each nonselected color a distinct asymmetric orbit and reverses the rare color's numeric rank across the first two demonstrations, while preserving matched inputs between settings.
- **Coverage:** supports independently selected 2–6 demonstrations and 1–4 queries; always retains four distinct controller-side queries, including a substantive 30x30 case. Public first-turn projection is prefix invariant and keeps settings/programs/answers private.
- **Evidence:** focused task tests passed; the 128-seed finite rival audit covered both settings and every demo count 2–6 for 1,280 episodes / 10,240 labeled pairs with zero harmful declared-rival survivors; authoring preflight, protected-Racket causal replay, and public projection checks passed.
- **Limit:** this is reviewer-ready source, not owner acceptance. The next action is exact-source native owner qualification, witness replay, and fresh acceptance after integration.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
