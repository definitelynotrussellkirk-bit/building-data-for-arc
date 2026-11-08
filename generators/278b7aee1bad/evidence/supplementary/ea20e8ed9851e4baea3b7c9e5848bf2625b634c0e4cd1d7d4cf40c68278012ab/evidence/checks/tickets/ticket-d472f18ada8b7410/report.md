# Bounded adversarial witness for `278b7aee1bad`

Pinned generator SHA-256 `bbc421bc61cbde919359452e033509ceb3ee81cd6788e3fb0be938f88507f35e` and rule hash `99a84b189ddf` matched.

The plausible **perpendicular-crossings-only** rival fits all 5 canonical pairs. It treats overlap output as occurring only where a horizontal and vertical span cross, so it ignores cells covered by two parallel collinear spans.

The ticket-seeded search examined 33 unchanged generator draws and found a lawful separating input at difficulty `hard`, seed `1458672832`, sample index `37739`. `self_check` returned no errors. The canonical Racket output matched the independent span-count implementation and differed from the rival at 2 cell(s).

This is a completed source-bound witness, not a no-issue safety record: it proves the generator can emit a refutation, but does not measure whether assembled lessons reliably include one. Existing unresolved audits remain unresolved.
