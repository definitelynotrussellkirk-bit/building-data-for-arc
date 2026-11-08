# Transfer-orientation parametric family

This task-local family keeps the selected canonical program byte-for-byte as
`orientation=direct`.  `orientation=rotate_180` first infers the bbox-aligned
A-to-B added-cell mask and its edit-frame dimensions, rotates that input-derived
mask by 180 degrees, then stamps it onto C.

The input stream is setting-matched and prefix-stable.  It supports 2–6 visible
demonstrations and 1–4 private queries; the first two demonstrations include an
in-bbox edit and a simultaneous row/column expansion.  Query four is a genuine
30×30 rectangular-panel extension of the same rule.  Settings, programs, future
queries, and query labels remain private.  This is authoring evidence only until
exact-source owner qualification and acceptance.
