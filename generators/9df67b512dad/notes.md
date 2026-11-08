# Current decisions: 9df67b512dad

## Canonical teaching repair

The canonical rule compresses the nine boundary/interior regions to 3×3 and picks the last nonzero cell in row-major order. Keep the rule, sampler, distribution, version, and schedule unchanged.

`lesson_identifiable` now rejects a declared rival only if it fits every lawful demonstration and changes the validated query answer. Requiring all scheduled masks inside the demonstration subset rejected valid held-out rotations and lawful unscheduled masks; that requirement is removed. The four-demo minimum and input/output validation remain. An answer-equivalent surviving rival is acceptable for the current query.

Evidence in return `review-af7e8164487a8e29`: the exact inherited witness (easy seed 191938644734028, start 0, query 1) retains all five inputs and Racket labels, with hook warnings reduced from three to zero across its five rotations. The strict finite gate passes 12 lessons and 60 rotations. The combined stock staged task test run passes 86 cases, including 15 canonical and 65 prototype cases. Only the hook changes in the production source.

## Separate proposed parameter prototype

`workspace/parametric/prototype.py` exposes two episode-fixed parameters: `scan_order` (row_major/column_major) and `pick` (first/last). The default row_major/last returns the exact formatted canonical Racket source. Demo and query counts are independent, each 1–8; default 2/4. A paired input seed makes settings directly comparable.

Sampling admits 5–14 rows, 7–16 columns, 4–8 occupied zones and no solid foreground 2×2. The prototype uses five distinct foreground colors, extending the current canonical generator's 1–3-color sampling range. A four-color interior diamond distinguishes all four selectors, and an occupied top boundary with a fifth color defeats the global-first occupancy rival. This is deliberately narrower than the input grammar.

Demonstration-only Racket inference eliminates the four-setting rivals and occupancy rival before query labeling. Export replays all labels, recomputes certificates, rejects malformed private provenance before writes, separates public/private output, and hashes only exact visible bytes. Independent review found and verified repairs for missing-seed partial writes and null settings provenance.

The retained four-setting export has eight demonstrations and sixteen queries, six distinct inputs per episode. These checks establish only finite-rival identifiability on retained examples; they do not establish arbitrary-rule uniqueness or learning benefit.

## Remaining work

Maintainer action: assess the narrow canonical hook repair and the separate parameter proposal before registering variants or admitting data. No approval or audit-status records were edited.

Pre-existing limitation: canonical output comparison accepts numeric-equivalent float labels through Python equality; prototype output validation is strict. The inherited test's legacy staged-import advisory remains nonblocking. Broader production batteries and seed censuses were not run because the sampler and canonical rule are unchanged.

Full source hashes, exact command receipts, regressions, Racket outputs and current limits are in the return's `RESULTS.json` and `checks/`. The separate peer finding for `71982ba2b59e` belongs to that return's audit ticket.
