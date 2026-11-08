# Working notes: 659980b6f715

## Final review state

- Canonical rule hash pinned: `df22257022fe`.
- Generator version: `4.0.0`.
- Final generator SHA-256: `bebd25d2975afcdaa7730e1d6d76bfe9f81b2ea7706cf4ac558f3b9c4e59fcec`.
- Final battery: 12/12 green.
- Portable task tests: 52/52 pass.
- Three-demo lesson census: 300 lessons, 1,200 query rotations, zero declared-rival ambiguity/errors.

## Root causes repaired

1. Baseline operands could use color 9, colliding with the fixed output overlap marker. Exact old witness: `counterexamples/reserved_marker_collision.json`.
2. The old control surface advertised dead/singleton axes and degenerate textures, accepted malformed scalars, and produced 10,038 override findings.
3. `RULE_HASH` and a strict lesson-level semantic contract were missing.
4. Selected executable Racket text was cosmetically divergent from canonical.
5. The first strict seed validator incorrectly imposed a small integer ceiling; profile census uses larger nonnegative integers.

## Design

Generation is constructive. Two connected path-prefix families of 4–8 cells always have a nonempty normalized intersection and unique cells on both sides. A shared random D4 transform provides orientation variation. Components are placed in opposite horizontal edge bands and at different top rows. Color 9 is reserved; operands use 1–8.

Public axes are only `grid_h`, `grid_w`, `low_color_cells`, `high_color_cells`, and `row_order`; `observe_overrides` recovers all five exactly.

Declared rivals test higher-color overlap, intersection-only output and bottom-right alignment. `EXAMPLES_NEEDED = 3` and every three-demo window is tested against all declared competitors.

## Parameter prototype

`workspace/parametric/alignment_anchor.py` proposes an episode-level `alignment_anchor` setting (`top_left` or `bottom_right`). It executes both rule programs through Racket and keeps public/private exports separated. Evidence: `checks/parametric/alignment-900/report.json`. This is proposed only and does not change canonical production.

## Remaining limitation

The constructive shape family is finite. Current evidence certifies the advertised manifold and declared rivals, not all possible polyomino distributions or hypotheses.
## Current reviewer considerations

Source SHA-256: `bebd25d2975afcdaa7730e1d6d76bfe9f81b2ea7706cf4ac558f3b9c4e59fcec`.

# Decisions: `659980b6f715`

## D1 — Preserve the canonical rule

The Racket semantics were correct and all visible canonical pairs matched. I changed the input curriculum, validation and teaching contract rather than altering the rule. The selected bank's executable `target_code` was synchronized to canonical only after execution parity passed; archival `raw_code` was preserved.

Rejected alternative: reinterpret color 9 as a legal operand. That creates a real observational collision: when the higher operand is 9, “paint overlap 9” and “paint overlap with the higher operand” produce identical labels.

## D2 — Reserve color 9

Operands are sampled from 1–8 and `self_check` rejects input 9. The exact old draw at seed 0, sample index 2, easy is retained in `counterexamples/reserved_marker_collision.json`.

Rejected alternative: keep 9 and rely on other examples to disambiguate. A single ambiguous example weakens labels, and a lesson can accidentally contain only such cases. Avoiding the collision is cheaper and semantically exact.

## D3 — Use constructive paired shapes

The low/high shape families are connected prefixes designed so every 4–8 by 4–8 size pair has a shared normalized region and unique cells on both sides. Both receive the same random D4 transform, then are placed on opposite horizontal sides with different top rows.

Rejected alternative: retain random-polyomino rejection loops. They made exact joint overrides hard to guarantee, allowed fallback behavior, and obscured whether all advertised combinations were reachable.

Trade-off: the constructive family is finite. The final diversity and lesson tests are strong for this family, but do not claim exhaustive polyomino support.

## D4 — Advertise only observable controls

The old `palette_kind`, `shape_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `overlap_kind`, and texture controls were removed because they were dead, singleton, aliases or deliberate degeneracies. The five retained controls are exactly recoverable by `observe_overrides` and every joint combination is tested in all four bands.

## D5 — Separate structural validity from teachability

`self_check` defines the strict generated manifold. `_predict` mirrors the canonical transformation for tests. Three named semantic rivals and witnesses test whether complete three-demo lessons teach the intended distinctions. This keeps malformed-input diagnostics separate from lesson-level ambiguity.

Rejected alternative: treat correct labels on individual grids as sufficient. That does not prove a lesson refutes shortcuts.

## D6 — Accept arbitrary nonnegative integer seeds

The first validation pass capped seeds too narrowly and failed the profile census seed `104903813062390`. The contract now rejects bool, negative and non-integer values but does not impose an artificial uint32 ceiling.

## D7 — Parameter extension remains isolated

`alignment_anchor` is a suitable episode-level extension because the setting can remain hidden, is executable in Racket, and changes query labels under unequal operand extents. It lives under `workspace/parametric/`, has separate tests/evidence, and does not change the canonical generator or authority.

## 2026-10-25 native parametric return

The retained alignment idea was promoted to a bounded native adapter without
changing production `generator.py`. `alignment_anchor=top_left` is byte-exact
canonical; `bottom_right` derives per-color bounding-box extents and uses them
to translate both normalized components before overlap marking. The new sampler
supports 2–6 demonstrations and four sequentially projected queries, including
a substantive 30×30 boundary case. A finite eight-policy audit, native
qualification and protected-Racket wrong-intermediate witness are the current
review evidence. Owner acceptance and training admission remain pending.
