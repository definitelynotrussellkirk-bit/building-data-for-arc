# 9c3781759581

Crop the **inclusive bounding box of all color-9 cells**. The topmost,
bottommost, leftmost, and rightmost markers determine the output rectangle.
Copy every cell inside that rectangle, including zero cells and other colors;
discard cells outside it. The unchanged Racket rule performs both row and
column cropping. Color 9 need not form divider columns or a connected object.

The **v3.0.2 repair candidate** samples sparse diagonal pairs, reverse-diagonal
pairs, and scattered markers whose side extrema require considering all 9s.
Default samples use a zero background, retain payload inside the marker box,
and place payload outside it to distinguish marker-defined cropping from
cropping all nonzero cells. Paired samples retain sparse payload. Default
scattered samples include one payload color occurring more often than color 9 and a
second payload color occurring exactly twice; additional payload multiplicities
vary within the available space. Default scattered inputs have at least four
distinct colors. These constructions supply witnesses against the declared
frequency rivals; they do not establish immunity to arbitrary frequency rules.

| Exact control | Supported values |
|---|---|
| `height`, `width` | 6..30 |
| `box_h`, `box_w` | 3..28, subject to canvas size and marker capacity |
| `marker_count` | 2..8; `scattered` requires at least 4 |
| `n_distinct_colors` | 3..10, counting zero and 9 |
| `texture` | `canonical_pair`, `anti_diagonal`, `scattered` |

Controls are checked against the generated pixels. Unpinned choices adapt to
valid pinned controls; incompatible joint requests raise explicit errors.
An exact full-canvas box is supported. Exact `n_distinct_colors=3` remains
supported, including for scattered inputs, outside the default lesson promise.

The sampler's construction domain is narrower than `self_check`: the validator
accepts any rectangular 1..30 by 1..30 grid of literal integer colors 0..9
containing at least one 9, including singleton and one-dimensional crops.

`EXAMPLES_NEEDED=4` requests four demonstrations. The declared semantic schedule
has period 12, combining three size/palette profiles with a four-position
paired/scattered pattern. Review evidence checks all five query holdouts of
five-pair lessons against nine declared rivals. These are finite checks on
the recorded seeds and source bytes, not a proof against all alternative rules.

Kind: `per_puzzle`. Candidate version: `3.0.2`. The canonical rule pin
`RULE_HASH = "a489a823697d"` is unchanged. Approval is derived by the catalog
from the current code and accepted evidence. The separate `target_color`
extension in `workspace/parametric/` is a proposed, unapproved prototype.
