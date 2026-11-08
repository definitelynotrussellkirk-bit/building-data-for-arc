# d94e8b169413

9x9 0-bg grid with exactly one non-zero corner marker. The marker color names the target color. Usually a same-color target object is placed in the body and 1-2 non-marker distractor objects are placed outside its bbox; sometimes the corner marker is the only cell of that color, yielding the canonical 1x1 fallback answer. Rule: choose the non-zero corner color and output the tight crop of cells with that color, excluding the corner when body cells exist.

Kind: `per_puzzle`. Imported version: `2.3.0`.
Approval is derived by the catalog from current code and retained evidence.
