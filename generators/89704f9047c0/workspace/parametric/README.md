# Nearest-corner tie-preference family

This task-local family preserves the canonical four-corner input grammar and
nearest-Manhattan-corner rule. Two episode-fixed settings choose which row and
column side wins exact ties:

- `row_tie`: `top` (canonical) or `bottom`
- `column_tie`: `left` (canonical) or `right`

The default `{row_tie: top, column_tie: left}` returns the canonical Racket
program byte-for-byte. Inputs are setting-neutral. The first two demonstrations
constructively isolate row and column ties, so every setting is the sole finite
survivor with the minimum two demos. Supported counts are 2–6 demonstrations and
1–8 prefix-stable queries; the ordinary four queries are distinct 29×30, 30×29,
29×29, and 30×30 scenes.

`prototype.public_turn(episode, i)` emits all demonstrations and exactly query
`i` without its answer, private settings/program, future inputs, or total-count
markers. IDs use `reviewer_support.public_challenge_id` over those visible bytes.
The adapter is ready for native worker qualification; this prototype is not an
approval or training-admission decision.
