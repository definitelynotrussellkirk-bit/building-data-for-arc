# Diagonal-span bracketing — public parent 7666fa5d

## Design and implementation plan
The three original labelled examples agree with a general rotated-coordinate rule. Extract each uniform northeast/southwest stroke as (u=r+c, low=r-c, high=r-c, length, color). A cyan cell becomes red exactly when its v=r-c lies in the continuous inclusive span of a stroke on each side in u. Preserve original strokes. Brackets may be nonadjacent; separated collinear segments remain separate. This is not an axis-aligned hull or isolated diagonal-ray fill.

The canonical setting is all_spans. The complementary equal_length setting requires both bracketing segments to have equal measured length. Segment extraction is A; the ordered spans and lengths are the input-dependent intermediate; geometric pairing and filling are B. Both settings receive identical inputs and four independently shuffled queries.

1. Fail original-label, hand-computed geometry, sampler and public-writer tests before implementation.
2. Implement the Racket rule, independent Python oracle, deterministic sampler and thin native adapter.
3. Attack the minimum lessons with total executable rivals, fix concrete counterexamples, and test protected parity.
4. Finish source-bound staged tests, authoring preflight, causal replay and single-query public export.

## Scope decisions
Cyan 8 is background and red 2 is newly filled area. Source colors may be any other ARC color. The canonical source grammar uses parallel negative-slope unit diagonal strokes. No assertion is made about arbitrarily bent strokes or positive-slope families. Equal-length matching and multicolor scenes are generative extensions, not evidence that the original parent selects those alternatives. Finite lesson checks do not prove universal identifiability.

## Current evidence and handoff
The final direct and staged suites each pass 37 tests. All three supplied original labels, including test gold, match protected Racket. The 32-seed audit covers 64 episodes, 1,280 demo/query prefix checks, 256 public projections, thirteen named rivals (832 lesson checks), and 88 protected-Racket evaluations, with no dangerous survivor.

Adversarial self-review found two genuine minimum-lesson gaps: both old demonstrations had only four strokes and no stroke longer than thirteen cells. The first-four and length-at-most-thirteen rivals each produced protected match results [true, true, false] on the old lesson and stress query. The revised second demonstration is a 29x29 scene with eight strokes and maximum length 21; both rivals now fail a demonstration. Retained regressions replay the old counterexamples and test the repaired lesson. See tests/fixtures/count-length-counterexample.json and checks/public_eval_7666fa5d/curriculum-before-fix.json.

Both settings pass the four-job authoring preflight at seeds 17/43, with two demonstrations and four queries. The causal witness replaces measured continuous spans with points in the equal-length setting, and a separate protected replay confirms a changed output. Sixteen saved one-query public files pass the public checker. The 30x30 stress input contains eight strokes and 112 nonbackground cells; the canonical result has 568 nonbackground cells and the equal-length result has 512.

The task-local audit checks matched inputs, independent prefix stability, declared rival identifiability, protected Python/Racket parity, and public redaction. Public export validates current preflight bindings, rejects duplicate payloads before writing, and emits sorted visible-byte IDs without settings, answers, or future inputs. Source-bound witness/export tools are self-contained within this home and have no predecessor imports. Final source review is author self-review. Owner registration, source approval, native qualification, acceptance and training admission remain pending.

## Reproduction
From the packet root, run `python3 review.py task-tests public_eval_7666fa5d --out ../checks/public_eval_7666fa5d-tests-final --phase after` into a fresh destination. Under `review.py run`, use the task-local `audit_native.py audit --seeds 32 --out PATH`, `audit_native.py export --preflight PATH --out FRESH_PATH`, and `authoring_witness.py --preflight PATH --recipe PATH --out FRESH_PATH`. RESULTS.json records exact payload commands and evidence paths.

Owner worker API correction: use the existing worker input/findings contract. Earlier author checks used the incompatible return convention. Reference programs are unchanged; owner preflight and native acceptance determine current readiness. See evidence/owner-base-api-repair.json.
