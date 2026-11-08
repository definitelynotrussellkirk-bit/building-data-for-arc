# Rules

1. Infer tile size from the first horizontal separator and parse 2–5 top-bank
   templates, each keyed by its unique nonseparator source color.
2. Merge the middle panels into one sparse n×n macro canvas. Token identity is
   the visible token color; panel position is irrelevant.
3. Parse the bottom palette block for each source color.
4. `self` expands each token through its own template and palette entry.
   `next_token` uses the next occupied row-major token cyclically.
5. The output is n²×n², with each occupied macro cell receiving the selected
   recolored template.
