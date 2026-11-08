# `924a6f0f0549` render-mode family

The episode chooses one finite `render_mode`:

- `outline` — exact canonical default, byte-for-byte.
- `silhouette` — after the same marker-count selection, render every selected
  object cell instead of only its 4-neighbor boundary.

The input sampler is independent of the setting. Every selected rectangle has
an interior, every episode contains 2–6 demonstrations and exactly four
queries, and the last query is a substantive 30×30 case with a 5×5 selected
object plus four differently sized distractors. Protected Racket remains the
qualification authority; Python labels are claims for replay.
