# d9d4f0ebb48b parametric family

This native adapter exposes one finite episode parameter:

- `fill_color_mode=local` — the exact approved canonical rule. Every true monochrome plus fills its own 3×3 footprint with its local color.
- `fill_color_mode=selector_source` — a contiguous unary marker in row zero selects a true plus in reading order. Its center color is the step-A intermediate, and step B fills every true-plus footprint with that color.

The sampled inputs are setting-neutral and deterministic by `(seed, pair_index)`. Episodes support 2–6 demonstrations and exactly four queries. The first seven examples always include 9×9 and 30×30 cases. Row zero is reserved for the selector; distractors never alter it. Python outputs are claims only—the native qualification worker re-executes all retained labels through protected Racket and checks demonstration-only finite identifiability.
