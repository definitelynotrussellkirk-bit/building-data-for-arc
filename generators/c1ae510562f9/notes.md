# Current decisions — c1ae510562f9

## Production authority and preserved contract

Production remains v2.1.0 with generator SHA-256 `10e6c120e80e377a8ca4e8c089d2bec293e784534b12f0740f7c029089ffc971` and canonical rule hash `7a7c1a560527`. Canonical Racket finds the gray U's extrema, counts rows in `[min-gray-row,max-gray-row)` whose cells strictly between the gray walls are all zero, and paints that count along the clockwise 3×3 cyan spiral, saturating at nine. Colors 0/5/8 retain their roles. The exact canonical source SHA-256 is `5f4c423c7710aea9644f31f4af2245279f4bd2879237980c7f428b9184adfd82`.

The production call contract remains strict: literal integer seed, nonnegative literal integer sample index, difficulty in None/easy/medium/hard, and exact coupled size/count controls. Negative integer seeds remain valid in production. Ordinary sampling stays within canvas 5..16 by 6..16, interior height 2..12, width 1..10, empty count 0..10, and the four-slot canonical/contrast-one/edge/contrast-two schedule. Explicit controls can remove teaching witnesses; production lessons still need their actual finite-rival hook.

The validator's upright-U grammar admits broader arbitrary interior 0/8 masks and canvas sizes through 30×30, with at least one cyan cell and no exterior cyan. The historical domain/control/one-versus-two-complementary-pair repairs remain current. Their counterexamples and retained review receipts remain provenance; the historical full batteries and 300-lesson census were not rerun in this return. No current open audit is listed in the task's review index.

## Native extension: reuse both existing rules

`workspace/parametric/spiral_direction.py` is unchanged. The new adjacent `native_family.py` and thin `adapter.py` reuse its exact clockwise and counterclockwise rule strings and claim mirror. The default is byte-equal to the canonical authority; both complete programs execute through the native protected worker. Production source, canonical ledger, approval records and shared runtime were not changed.

The native parameter is episode-fixed `spiral_direction=clockwise|counterclockwise`. It supports 3–6 demos and 1–4 queries independently, with exact integer seeds 0..2**63−1. Settings share all input draws for a given seed. Fixed seed/slot RNG streams preserve prefixes under count changes; duplicate retries are bounded; no short batch is silently emitted. Outputs are fresh and global RNG state is untouched.

A recovers strict interior bounds and the wholly empty row set/count. B consumes that count to select a spatial spiral prefix. A same-histogram cyan relocation regression changes the true count from five to four and the output by one cell. The current native causal witness executes zero-area/width as a wrong intermediate on the five-row demonstration, yielding six instead of five, for both spiral directions.

## Teaching repair and current sampling

Independent self-review found a concrete cap-six shortcut: the draft's counts 5, 6, 2..4 demos all matched it, but an eight-row query differed. `checks/c1ae510562f9/cap-six-original-lesson.json` preserves that complete original generated three-demo/query lesson, both programs, actual labels/runtime identities and the old source identity. It is not an official canonical lesson, current generator output, or alternate official answer.

The final minimum-three lesson teaches counts 0, 5, 9+:

- A zero-count example has six nonempty partial rows in three complementary pairs. Every column contains three zeros, yet no row is wholly empty. Singleton cyan at both interior edges defeats dropping a column and zero output defeats positive floors.
- A five-count example has one complementary pair and empty first/last interior rows. Its area/column deficit differs from the zero-count example; it teaches exact row boundaries and the spiral direction.
- Nine to twelve empty rows above solid bottom fill teach saturation, refuting caps below nine. The third demonstration is essential; two-demo requests are rejected. One audit constant controls all three-demo screening slices and metadata.

Extra demos vary occupied masks, dimensions and placements. Queries cover compact zero/one endpoints, count-eight/saturated endpoints, large unsaturated counts, and a full 30×30 U with 29×28 interior and unsaturated count 2..7. Substantial cyan contents and gray boundaries span the full canvas. Output remains 3×3 by rule. The first three teaching regimes and fixed semantic colors restrict diversity; ordinary production controls are unchanged.

## Current executed evidence and status

- 52 focused tests passed across the new adapter/audit tests and retained prototype tests. They cover all seven official pairs, exact program reuse, same-histogram causality, endpoints 0/1/8/9/28, saturation, cap/floor repair, count/seed/grid typing, prefix independence, fresh results, and strict export rejection cases.
- `checks/c1ae510562f9/audit-final/report.json`: seeds 0/17 × two directions, four episodes, 28 intended labels, 224 episode/candidate comparisons, 664 protected Racket evaluations and 36 cache hits. All candidates were refuted on the first three demonstrations. Cap-six is specifically refuted by demo index 2 in each episode. The report does not claim 224 unique programs or universal identification.
- The reusable audit exports 16 canonical hash-named, strictly masked one-query public files. It checks duplicate/forged/malformed/public-field/private-label/unindexed-file cases. `public_turn` reveals no seed, setting, program, answer, future input, index, total count or final-turn flag. First turns agree for one-query/four-query use with the same demos. The consumer controls sequencing.
- The refreshed task-local source manifest and `checks/c1ae510562f9/qualification/qualification.json` bind current bytes. Native qualification passed four jobs with 3 demos/4 queries, 40 protected evaluations. Both causal cases in `checks/c1ae510562f9/causal/witness.json` executed and replayed with different final outputs.

Reviewer status is **ready**, with the demonstrated teaching gap repaired. Owner qualification and fresh native acceptance of the exact integrated source remain mandatory; this return performs neither acceptance nor training admission. Finite seeds/rivals do not establish every-seed correctness or measured learning gains. Causal intermediates remain authored interpretation; replay verifies final labels. Serialized export verification is not a new Racket replay or authentication of an entirely rewritten bundle.

`workspace/parametric/README.md` gives current runnable commands. The old five-fixture evidence under `evidence/retained/` and the associated historical notes remain prior provenance, not current native qualification.
