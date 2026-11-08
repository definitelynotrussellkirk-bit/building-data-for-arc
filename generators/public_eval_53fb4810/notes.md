# Patterned beam completion — public parent 53fb4810

## Design and implementation plan
Author the original general rule: find blue anchors and attached complete-width color strips, measure the observed strip word and its shortest repeating period, then extend each incomplete beam to the boundary. Existing seed cells remain unchanged; an extension may overwrite another already-complete trail, as in train 0. Use repeat as the default and a taught ping-pong continuation as the complementary setting. The extracted word, width, direction, and phase are the input-dependent intermediate consumed by extension.

Implement and test this home before starting the other assigned target. No catalog/shared-runtime/approval modifications. Source extraction is isolated; the packet is not a Git checkout, so its frozen hash baseline is the patch authority.

1. Write failing original-rule and sampler/contract tests.
2. Implement a pure Python oracle and deterministic matched-input sampler; preserve reference bytes in canonical.rkt.
3. Attack minimum lessons with finite executable rivals and retain concrete findings. Verify both settings in protected Racket.
4. Run staged task tests, authoring preflight, source-bound causal replay and one-query public export checks.

## Scope decisions
The canonical colors are blue 1 for anchors and cyan 8 for background; every other color is legal in a beam. Generated beams are cardinal, contiguous, complete-width strips. The provided originals establish periodic repetition but do not uniquely determine arbitrary damaged/multidirectional inputs. Those are excluded from this grammar. Completed input strips, including irregularities in the original test, are never repaired. Overlap between two newly extending beams is not sampled; an existing complete beam can be crossed by one new extension. The alternative is a new generative rule, not original-task authority.

## Current evidence and handoff
The final direct and staged suites each pass 33 tests. All three original labels match protected Racket, including the train-0 crossing overwrite and the test input's already-complete irregular trail. The 32-seed audit covers 64 episodes, 1,280 demo/query prefix checks, 256 public projections, eleven named rivals (704 lesson checks), and 80 protected-Racket evaluations, with no dangerous survivor. This is a finite result, not uniqueness among arbitrary programs.

A concrete width-gated rival originally fit both demonstrations because the width-three strip in the second demonstration was already complete. The retained old lesson/query produces protected match results [true, true, false]. The first demonstration now contains an incomplete width-three strip, and the regression replays the old counterexample and rejects the rival on the repaired lesson. The exact old grids and executable rival are in tests/fixtures/wide-strip-counterexample.json and checks/public_eval_53fb4810/curriculum-before-fix.json.

Authoring preflight passed both settings and seeds 17/43 with two demonstrations and four queries. The causal witness forces period one instead of the observed input-specific period and has a separate protected replay. Sixteen saved one-query public files passed validation. Public files are named and emitted in sorted visible-byte SHA-256 order; the private manifest preserves shuffled presentation. Duplicate public payloads are rejected before the destination is created. Reversing private episode enumeration produces identical public bytes.

No owner approval, native qualification, acceptance or training admission is claimed. Source-bound witness/export tooling was copied from the packet's existing public-authoring implementation into this home; it has no predecessor imports. Final source review is author self-review, not independent review.

## Reproduction
From the packet root, run `python3 review.py task-tests public_eval_53fb4810 --out ../checks/public_eval_53fb4810-tests-final --phase after` into a fresh destination. The task-local `workspace/parametric/audit_native.py audit --seeds 32 --out PATH` reproduces the bounded audit under `review.py run`. Its `export` command accepts a current preflight receipt and a fresh destination. The adjacent `authoring_witness.py` accepts `--preflight`, `--recipe`, and `--out`; it rejects stale source and receipt hashes. See RESULTS.json for the exact payload commands and retained paths. Do not promote authoring evidence to owner acceptance.

Owner worker API correction: use the existing worker input/findings contract. Earlier author checks used the incompatible return convention. Reference programs are unchanged; owner preflight and native acceptance determine current readiness. See evidence/owner-base-api-repair.json.
