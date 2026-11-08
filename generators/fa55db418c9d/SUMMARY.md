# fa55db418c9d — exact blue L-triomino recoloring

**Generator version:** `3.0.1`  
**Canonical rule hash:** `eeee12543bcc`  
**Authority:** the canonical Racket program is unchanged and remains the output oracle.

## Rule

Treat nonzero cells as same-color, cardinally connected components. A component changes only when all of these are true:

1. its color is blue (`1`);
2. it has exactly three cells;
3. its bounding box is `2×2`; and
4. those cells occupy an L-triomino, leaving exactly one corner missing.

Recolor the whole component by the missing corner:

| Missing corner | Output color |
| --- | ---: |
| southeast | 2 |
| southwest | 3 |
| northeast | 4 |
| northwest | 8 |

Every other component is unchanged, including blue straight triominoes, larger blue shapes, and non-blue L-triominoes.

## Generated curriculum

A deterministic five-profile schedule (`sample_index % 5`) supplies one canonical-scale/palette anchor and four contrast profiles. Across every complete five-example lesson it covers:

- all four target orientations;
- a blue straight triomino;
- a blue component larger than three cells;
- a non-blue L-triomino; and
- an edge-touching target.

The schedule is shared across easy, medium, and hard bands; the bands mainly change available canvas size. Default profile 0 reaches the four-color canonical palette `{0,1,6,7}`. Profiles 1–4 use different blue non-L shape families and include a non-blue L counterexample.

## Exact controls

The only advertised controls are directly observable and exhaustively tested:

- `grid_h`: `9..20`
- `grid_w`: `10..22`
- `n_target_l`: `1..4`
- `n_blue_decoys`: `0..1`
- `n_colored_l_decoys`: `0..1`
- `target_position`: `interior | edge`

Unknown controls and unknown difficulty names reject loudly. Explicit controls omit hidden canonical decorations so all boundary combinations remain feasible.

## Semantic contract

`SEMANTIC_WITNESSES`, `LESSON_COMPETITORS`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, and `lesson_identifiable` are executable. The strongest canonical-fitting shortcut is **“recolor every blue size-three component.”** It fits all five public pairs but is refuted by profile 1’s blue straight triomino.

## Scope

The generator deliberately uses a one-cell cardinal moat for visual clarity. That is a sampling policy, not a rule restriction: `self_check` accepts lawful same-color component scenes such as canonical examples with cross-color contact. The measured curriculum probe is finite evidence for the emitted default domain, not a claim of universal rule induction.
