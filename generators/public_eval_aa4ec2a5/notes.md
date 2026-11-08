# Public creation notes: aa4ec2a5

## Rule and explicit extension

Infer the unique modal background and extract four-connected foreground objects. Flood each object's bounding-box complement; regions unable to reach the box edge are cavities. Recolor every foreground pixel of a cavity-bearing object to 8, fill its cavities with 6, preserve cavity-free foreground, and add a clipped, one-cell eight-neighbor exterior outline in 2 around the filled support.

The episode setting is `hole_connectivity: 4 | 8`, default 4. Four requires orthogonal background paths; eight permits diagonal escape. All four official labelled pairs agree under both choices. Default four is an explicit extension, taught by fresh diagonal apertures. Foreground connectivity remains four and outline connectivity remains eight.

The domain is exact rectangular integer grids with axes 1..30, exactly two colors from 0, 1, 3, 4, 5, 7, 9, and a unique modal background. Separate foreground four-components cannot touch diagonally; foreground nested in another object's four-connected cavity is excluded under both settings. This makes component-local cavity ownership explicit. Long arms, multiple cavities, open concavities, overlapping outlines and clipping are supported. Output colors 2, 6, 8 stay fixed. Python validates this domain; Racket assumes it.

## Construction and binding

Ten finite constructive geometry profiles supply six demos and four novel queries, varied by seeded palettes and global D4 transforms. Both required cores combine closed/diagonal cavities, long arms, open concavities, solids, singleton clipping and outline overlap. Distinct 30×30 demo/query profiles have 353/388 foreground cells. The first two demos deterministically differ in both background role color and foreground role color; later palettes remain freely sampled. Construction has no retries or answer lookup. Queries are shuffled before prefix selection.

Counts are 2..6 demos and 1..4 queries; ordinary generation uses 3/4 and `qualification_demos` is the minimum 2. Root generator declares `RULE_TASK_ID = 'ee_aa4ec2a5'`. Reference and adjacent canonical resource are byte-identical; native reads the adjacent file. Canonical SHA256 is `95e67a7d41b1ac4c4a3e120f0482327f3063bd2dc3e1e35a099b44ee02f8909a`; normalized rule hash is `41fa9a387754`. Exact texts and both setting hashes are retained in the independent protected probe.

## Completed evidence and limits

Paths below are relative to `checks/public_eval_aa4ec2a5/`.

- `native-complete-v2.xml` and `audit-literals-v4.xml`: 48 native plus 101 independent audit tests passed. `sampler-v2.json`: 96/96 requests, zero failures, 159 distinct inputs, 64 query inputs and 32 distinct 30×30 inputs. Sampler v1 is historical; sampler structure alone does not certify Racket labels.
- `learned-foreground-hole-v1/report.json`: six protected evaluations preserve the old seed 15 failure, where a learned constant foreground fits both demos but fails a query. Old source/runtime and the failing `palette-diversity-red.xml` are retained. The repaired palette guarantee refutes learned background/foreground constants by the second demo in all six audited episodes.
- `design_protected_probe.json`: 12 independent protected checks passed on four official pairs and both core geometries under both settings. Read-only source review found no additional defect.
- `teaching-v1/private/audit.json`: all 64 labels passed (4 official, 60 generated); 174 fits yielded 168 refutations and 6 intended-only survivors. All 24 survivor query scores agree. This used 370 protected evaluations across 436 requests, with unchanged source/runtime.
- `preflight/preflight.json`: passed authoring preflight. `causal-observations.json`: four protected measurements; `causal/replay.json`: two cases constructed with four evaluations and replayed with four, status `reviewer_replayed`. The intervention empties only derived cavity lists; object coordinates and all downstream aggregation, filled-support, rim and rendering code remain unchanged.
- `preview-verify.json`: all 16 views across four episodes verified as projections of the preflight execution; this projection check does not itself rerun Racket.

Evidence covers finite seeds, ten geometry profiles, named rivals and two causal cases. It is not exhaustive geometry coverage or proof against all possible rules. No production, catalog, runtime or training state is changed. Owner registration, source review, native qualification at the declared minimum, and acceptance remain pending. Authoring preflight is not owner qualification or admission.
