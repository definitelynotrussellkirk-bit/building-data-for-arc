# Working notes: 1118c9143cae

## Final reviewer state — 2026-10-26

The imported base advertised controls that were dead, inconsistent, or silently accepted. The repaired `generator.py` is version 2.0.0 and keeps the canonical rule unchanged: every nonzero cell is retained and echoed at `(h - 1 - r, w - 1 - c)` in the same color. Its only public axes are now live and checked: `grid_h`, `grid_w`, `cell_count`, `n_colors`, and `scene_profile` (`interior`, `boundary`, or `fixed_point`). Unknown, wrongly typed, out-of-range, and incompatible overrides fail explicitly. Ordinary generation covers boundary contacts, odd-grid fixed points, and substantive exact 30×30 scenes.

The native family adds one episode-fixed parameter, `echo_scope`:

- `all`: exact canonical Racket program bytes.
- `rarest_color`: count nonzero colors, select the unique rarest color, then half-turn-echo only source cells of that color while retaining all originals.

The nondefault rule therefore has a real sequential dependency: color counts → selected color and selected source-cell set → reflected echoes. A protected-Racket causal witness forces the wrong intermediate color and changes the final output.

The family supports 2–6 demonstrations and exactly four distinct queries. Native qualification uses three demonstrations, while the adversarial probe separately attacks the two-demonstration minimum. Inputs are byte-identical across settings for the same seed/counts. The four-query bank includes dimensions 7×8, 12×17, 17×19, and a substantive 30×30 scene.

Deep self-review found and repaired three concrete shortcuts: the first sampler always selected color 7, always used rare count 2, and lacked a strict private-episode validator. The final sampler crosses rare colors 2–9, rare counts 2/3, and ranks 1/2 inside the minimum lesson. The validator binds source programs and labels and rejects wrong counts, duplicate inputs, malformed numeric/grid values, stale or forged programs, extra private fields, and ambiguous lessons.

Final finite evidence: 15 focused regressions; 48 two-demo episodes / 288 pairs against 25 relevant shortcut rules; 24 protected-Racket adversarial replays; native authoring preflight with 4 jobs, 28 parametric pairs, 4 canonical pairs, and 40 protected-Racket evaluations; 16 single-query public views; 24 first-turn hidden-field invariance checks; and four rejected projection corruptions. These checks do not prove universal uniqueness. Owner source review, fresh native qualification/acceptance, and any training admission remain separate and pending.
