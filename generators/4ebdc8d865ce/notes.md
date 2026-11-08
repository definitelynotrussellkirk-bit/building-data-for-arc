# Working notes: 4ebdc8d865ce

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/4ebdc8d865ce/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

<!-- review-8c56aafa9ed39b10:start -->
## 2026-10-24 parametric MAIN review (`review-8c56aafa9ed39b10`)

**Decision.** Keep the production generator and canonical rule unchanged. Add an opt-in, source-bound `target_degree` family under `workspace/parametric/`: `0` is the exact canonical rule and `1` recolors degree-one endpoints. Inputs are matched across settings and deliberately cover diagonal-only contacts, horizontal/vertical pairs, larger paths, branches, degree-2/3/4 cells, interiors, boundaries, and a 30×30 stress query.

**Sequential dependency.** Step A computes the orthogonal degree of every color-2 cell; the intermediate is the complete degree map; step B recolors cells whose degree equals the episode-fixed target. The protected-Racket wrong-intermediate witness substitutes eight-neighbor degrees and changes two final cells: `checks/4ebdc8d865ce/sequential-witness.json`.

**Current exact sources.** Production generator remains `943bbd19be3918848e6377245c7f264068812dc9331f0e19a97658d189927797`. Adapter `c1c9f583e6a92f56cf8f0d608d9e7edb069027b46c792a371ccc68f8034a8bf6`; prototype `93b8aaa9a789a2367a0e1b1a725841008cdafb53589775cc72e25c8256cf0395`; canonical program `99472c9502d886c3ad84ce6b2090f691cceb446ba067032ed54f62ffdaa4d271`; promotion contract `afa2d6709a97bfef83ea4d0fde57294019895a83e413495fb75fbbe6da135c7a`; inventory `79012b3922ee5df018a6754a93bede0354e7ff23b0226f60db2cf4dd889edb78`.

**Verification.** Focused suite: 11 passed. Changed-target gate: 19 tests plus 13 subtests passed. Reusable audit: four jobs, 32 protected-Racket labels plus two causal evaluations, exact matched inputs, prefix stability, strict public masking, finite declared rivals uniquely reduced to the intended rule after two demonstrations, and a 30×30 query with 151 foreground cells and 71 changes. Native qualification: two settings × two seeds × four queries, 32 protected-Racket evaluations. The independent witness replay executed two more protected-Racket labels.

**Limit and next action.** This is reviewer-reported readiness, not owner acceptance, universal identifiability, measured learning gain, or training admission. The owner should integrate these exact bytes, replay the source-bound witness, run fresh native qualification, and accept only if the live binding remains identical.
<!-- review-8c56aafa9ed39b10:end -->

<!-- arcpuzzles-owner-reconciliation:start -->
## Current parametric decision

Owner-native accepted `target_degree=0|1|anchor_area`. Both prior degree programs remain byte-exact. The new setting computes occupied anchor area before selecting whole color-2 components. All settings share anchored inputs and a boundary singleton teaching contrast. The old unanchored sampler remains a source capsule; it cannot enter this active bank because the new rule requires an anchor.

Fresh owner qualification passed three settings × two seeds, two demonstrations and four queries, with 60 protected Racket evaluations, followed by acceptance. Two protected counterfactual replays also confirmed the occupied-area versus bounding-box distinction. Current bindings and independent bounded audit: `evidence/owner-sampler-reconciliation/current.json`. Earlier source hashes and readiness claims above are historical provenance. Incoming direct delta remains deferred; this union is separately accepted. No model-training admission or unrestricted uniqueness is claimed.
<!-- arcpuzzles-owner-reconciliation:end -->
