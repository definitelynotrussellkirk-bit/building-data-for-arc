# Native parametric family

- `all_nearest` is the byte-exact canonical rule.
- `dominant_assignment` first assigns every gray blob to its nearest marker,
  aggregates assigned area by marker color, and retains only the unique largest
  assignment group while preserving every marker.

The family supports 2–6 demonstrations and 1–4 query prefixes. The complete
private bank always contains four distinct queries; query 4 is a substantive
30×30 boundary stress case.
