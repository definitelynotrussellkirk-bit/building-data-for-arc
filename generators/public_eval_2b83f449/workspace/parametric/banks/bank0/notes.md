# public_eval_2b83f449 — current design

Original mechanism: horizontal orange gates rotate into vertical magenta barriers,
joining the cyan tracks at their sides. Green tokens settle along each derived
simple track at its lower endpoint, packing without loss. Flat components retain
their original token locations. All labelled original examples, including test
gold, must agree before authoring preflight.

Variant: `sink=upper` reverses only endpoint choice after the same gate/topology
stage. Default `sink=lower` is exactly reference.rkt. The sampler preserves thin
nonbranching tracks, 3-cell gates and endpoint tokens, varies gaps, gates, rail
counts and canvas dimensions, and permits 30x30 with a one-row top margin.
No literal original input/output bank is used by generation or solving.

Implementation/check sequence: original-rule regression; graph and conservation
invariants; deterministic independent demo/query streams; protected Racket parity;
finite-rival teaching; one-query content-hash export; source-bound preflight and
wrong-topology causal replay. Changes are confined to this new task home.

Limits: endpoint direction is the explicit extension of the supplied examples;
flat components are stationary. No interpretation of branched marker tracks is
claimed; the generated grammar rejects them. Reviewer evidence is not acceptance.

## Verified handoff

- Authored a general rotating-gate/path-settling Racket rule and lower/upper endpoint family; 3/3 original labels, 31 tests, protected audit and authoring preflight pass.
- Two settings, 2–6 demos and 1–4 source queries; full four-query banks
  are shuffled separately for one-query public turns.
- Self-audit: 64 protected Racket labels, 66 stress episodes, 16 public views.
- Preflight: both settings at seeds 17 and 43, two demos and four queries.
- Causal replay: 14 changed cells with an intentionally wrong intermediate.
- Combined final suite: 63/63. Cross-target final review: 168 episode requests
  across every supported count, plus current source/evidence hashes and
  first-turn invariance under changed private metadata and future queries.
- Historical red logs are deliberate missing-implementation tests; the second
  target also records a corrected test-fixture parameter typo. No current
  failing check remains. This is author self-review, not independent review.

Reproduce from a packet root with `python3 review.py run python3` followed by
`generators/public_eval_2b83f449/workspace/parametric/self_audit.py --out ../checks/public_eval_2b83f449/fresh-audit`.
After any source edit, use a NEW preflight destination and rebuild the causal
witness with `--preflight ../checks/public_eval_2b83f449/preflight-v2/preflight.json --out NEW`.
The preflight receipt, execution, official-label report and causal witness are
authoring evidence only. Owner registration, source review, native qualification
and fresh acceptance are pending. Training admission remains false.

Current bound evidence uses preflight-v2, audit-v2 and causal-v2. Initial packaging exposed an exact-schema mismatch: the Racket marker must contain only backend/protected; full identity is now stored separately as racket_identity. The writer is fixed and both actual protected executions and source bindings were regenerated. The two owner-schema regressions now supplement the 63 task tests.
