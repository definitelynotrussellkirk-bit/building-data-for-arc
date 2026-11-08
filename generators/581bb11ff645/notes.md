# Working notes: 581bb11ff645

The canonical rule sorts complete red column groups by increasing black-cell
count. Production generator `3.0.0`, canonical program, and approvals are unchanged.

`workspace/parametric/` is a separate proposed extension of parent ARC training
task `42a15761`. It varies `count_mode` (`cells` / four-neighbor `components`)
and `direction` (`ascending` / `descending`), fixed once per episode. Default
materialization returns the exact canonical Racket text. Black regions stay
inside each group; boundary zeros count and score ties preserve input order.

The runnable exporter supports independent demo/query counts `1..16`, defaults
to three demonstrations and four distinct queries, and executes every label in
Racket. Queries include `21x29` and `30x29`; exact width30 conflicts with the
three-to-five equal-slot, single-separator geometry. Counts remain distinct in
generated scenes; tie/boundary behavior is covered by literal focused tests.

The first demonstration separates all four settings, both eight-neighbor
component shortcuts, identity, and reversing the groups. Query certificates
depend only on visible demonstrations and query inputs. Their finite rival set
does not establish universal identifiability or measured difficulty.

The public writer uses exact visible-byte hashes, sorts identities, and rejects
duplicates. Its separate replay verifier checks source/program identities,
strict integer labels, every parameter prediction in Racket, and certificates.
Seeds are retained metadata, not independently replayed provenance. See the
workspace README for the exact generation/test/replay commands and domain limits.

The separate accepted adapter now supports the four settings through the shared
`parametric` API; `parametric/accepted.json` is its exact-source authority. The
canonical generator and rule remain unchanged. Original prototype evidence
keeps its reviewer-reported/proposed status, and training admission stays false.

The adapter's inputs are counterbalanced across settings and use a separate RNG
stream. Direct delegation to the original setting-conditioned rejection sampler
gave two input streams for each fixed qualification seed; the adapter now admits
a common first demonstration that rejects the extra shortcuts for all settings.
This removes a sampling confound, without claiming a measured input-only shortcut.
Fresh protected qualification and acceptance replay cover all settings at seeds
0 and 17; separate count-boundary checks cover 1/16 and 16/1 requests. Evidence,
the source before the correction, and export commands are in
`evidence/owner-parametric-promotion/` and the workspace guide. Sampled score ties
remain outside the curriculum; expand rivals or add tie sampling for a concrete
teaching objective.
Imported associated notes remain in `evidence/associated_notes.jsonl`.
