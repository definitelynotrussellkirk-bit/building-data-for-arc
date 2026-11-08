# 0fcb77c31d06

Row 0 is a sparse legend with three or four nonzero colors and one unique
frequency winner. Rows 2 onward contain two separated objects in that key color
plus differently colored distractors. Select the largest 4-connected key-color
object, crop its bounding box from the input, and upscale the crop by a factor
of two.

Generated examples deliberately make the key non-leftmost, put a smaller key
object earlier in reading order, and include a larger non-key distractor. Thus
legend counting, connected-component selection, and “largest within the chosen
color” are all observable rather than recoverable by the canonical shortcuts.

Kind: `per_puzzle`. Current version: `3.0.0`. Canonical rule hash:
`c515fc7de0cf`. Approval remains a catalog/maintainer decision; passing review
checks does not itself approve training use.
