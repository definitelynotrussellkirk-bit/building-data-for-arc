# Solve notes — 0701a2c36d45

Earlier rule exposure: yes, from the generator-review phase. During this solve I did not reopen the generator, Racket rule, canonical labels, or prior solution explanations; I used only the prepared visible challenge.

## Visible-example hypothesis

The first row contains three control values in `1..4`. Three all-9 rows delimit three equally sized panels. Each panel contains one colored shape surrounded by zero padding.

Tight-crop each shape, then interpret its corresponding control as clockwise quarter-turn count plus one:

- `1`: identity
- `2`: 90 degrees clockwise
- `3`: 180 degrees
- `4`: 90 degrees counterclockwise

Place each corrected crop at the top-left of a blank panel-sized canvas. Output color 8 wherever at least two corrected masks occupy the same cell; output 0 elsewhere.

Example 1 is decisive: its code-2 first crop, code-4 second crop, and code-1 third crop all become the same top-left L shape, exactly matching the 8-valued output. Example 0 additionally shows majority voting rather than requiring all three masks to agree.

## Implementation choices

The parser finds all-9 separator rows rather than assuming fixed row indices. Shape color is ignored: every nonzero panel cell belongs to the mask. Rotation is applied to the tight crop, not to the padded panel, and the rotated crop is top-left aligned before voting. This also handles rectangular crops and the 6-row panel in visible example 3.
