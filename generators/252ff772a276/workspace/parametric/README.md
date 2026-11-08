# Winner-frame fill-scope family

The private episode parameter is `fill_scope`:

- `all_interior` is the exact canonical program: rank complete color-1 frames by
  interior color-2 seed count, top row, then left column; crop the winner and
  fill every remaining interior zero with green 3.
- `winner_seed_rows` preserves that ranking, then derives the winner's
  input-dependent set of seed-bearing interior rows and fills only zeros in those
  rows.

The sequential dependency is substantive: A selects the canonical winning frame
and extracts its seed-row set; B uses those row indices as the spatial mask for
painting. A protected counterfactual substitutes the runner-up frame's seed-row
set, changing the final crop.

The matched sampler supports 2–6 demonstrations and 1–4 prefix-stable queries.
Its retained four queries are 10×14, 16×20, 24×27, and a distributed 30×30 case
whose winning frame has at least 120 interior cells. Inputs are independent of
hidden settings and requested totals. Public projections expose all visible
examples plus one query input at a time, never settings, programs, answers, or
future queries.
