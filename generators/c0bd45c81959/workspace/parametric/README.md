# c0bd45c81959 native parametric family

- `all_modes` is the exact canonical fixed-six-block mode summary.
- `duplicate_bbox` first extracts the six block modes, finds the one mode occurring twice, then fills the macro-grid bounding box between those two positions.
- The fixed source layout naturally tops out at the ordinary 13×14 padded domain. A 30×30 input would add only ignored background, so this family records that limit instead of claiming fake large-grid coverage.
- Sampling is setting-independent, supports 2–6 demonstrations and four distinct queries, and deliberately places outliers in block anchor cells to defeat first-cell shortcuts.
