# Question: generator-shortcuts

**Exact question:** For this generator, name the strongest plausible shortcut or
rival rule that fits the canonical demonstrations. Give an exact input on which
it disagrees with the intended rule, how you checked the output, and whether your
proposed generator emits such cases.

## Answer

The strongest observed canonical-fitting shortcut is **`smallest_mover`**:
among qualifying mover/wall candidates, choose the mover with the smallest cell
area, using the intended nearest-gap ranking only to break area ties; then perform
the same channel cut, wall growth, and far-side relocation. It matches all 8
usable labeled canonical pairs.

The retained exact disagreement is
`generators/537b409b6744/counterexamples/smallest-mover-shortcut.json`, replayed by
seed `1`, sample index `17`, with overrides:

```json
{
  "grid_h": 10,
  "grid_w": 10,
  "direction": "down",
  "mover_span": 2,
  "mover_depth": 2,
  "wall_extra": 2,
  "wall_depth": 3,
  "gap": 1,
  "distractor_kind": "solid"
}
```

Its intended nearest candidate is color 0, area 4, gap 1; the shortcut selects
color 8, area 2, gap 3. I executed the selected canonical Racket program and
compared it with both an independent Python oracle and the rival. The Python
intended output matches Racket, while the rival output differs. The complete
input, both outputs, candidate table, changed cells, hashes, and command are in
`checks/shortcut/smallest-mover-evidence.json`.

The repaired v4.1.0 generator does emit such cases. The final semantic gate found
the witness on 317 of 600 strict draws. More importantly, task tests establish a
shortcut-refuting demonstration in every four-pair lesson window and every held-out
query rotation; the retained 300-lesson census reports the shortcut refuted in
300/300 production lessons and all 1,200/1,200 rotations.
