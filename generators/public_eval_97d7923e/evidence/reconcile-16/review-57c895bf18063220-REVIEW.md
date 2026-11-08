# Review return — `review-57c895bf18063220`
Assignment: create complete native public-evaluation families for `public_eval_4c416de3` and `public_eval_97d7923e`.
Status: **both reviewer-ready**; neither is owner-accepted or training-admitted.
Official parent labels: **4/4 protected-Racket matches per task**, including supplied test gold.
Focused tests: **12/12 per task; 24/24 combined**.
Authoring preflight: **4/4 setting/seed jobs per task**, with unique demonstration-only setting survivors.
Bounded adversarial audit: **640 episodes, 6,400 visible pairs, 4,160 declared-rival checks, zero query-changing survivors**.
Stress/public evidence: **128 substantive 30x30 queries and 32 hash-named masked one-query exports**.
Causal evidence: exact protected replays change **10 cells** for `4c416de3` and **26 cells** for `97d7923e`.
Source scope: only the two assigned generator homes changed; shared authority, catalog, approvals, and immutable parent data remain untouched.
Final review: read-only author self-review; no independent reviewer agent was available.
Remaining gate: owner registration, unchanged native qualification, exact-source acceptance of both builds, then any separate training decision.

## `public_eval_4c416de3` — corner-motif transport

Built a general canonical Racket rule and matched-input parametric family:

- `transport=reflect` is canonical: recover the complete source-corner motif, normalize it to top-left-relative offsets, and reflect it into every marker-only target corner using that target's color.
- `transport=rotate` applies quarter-turn transport on the same visible inputs.
- Generated motifs are intentionally asymmetric. The immutable parent's particular motif is diagonal-symmetric, so its labels alone do not distinguish reflection from rotation; this ambiguity is documented rather than hidden.
- Supports 2–6 demonstrations and four independently revealable, prefix-stable queries. Query presentation is privately permuted and no total-count hint, setting, program, answer, or future query is exported.
- Query four is a genuine 30x30 multi-frame case.

Verification retained under `checks/public_eval_4c416de3/`:

- 12/12 current-source focused tests.
- All four supplied labelled pairs matched protected Racket.
- 320 audited episodes, 3,200 visible pairs, 1,920 declared-rival checks, 128 cross-setting query disagreements, 64 substantive 30x30 queries, 34 protected-label evaluations, 16 protected-rival evaluations, and 16 masked public views.
- Declared rivals: identity, opposite transport, source-color copying, first-target-only, transposed motif, and unoriented copy.
- Source-bound counterfactual keeps only the first target record; protected replay changes 10 cells.

Exact hashes:

- Generator/sampler: `58566b863d2e54ff17c82050aa1b38664535d1711a8095f561bf94fe625f82ab`
- Canonical Racket: `541769c29d0391dfe9567d1f1f271b2bddc4ddf19d832a1010afd4aa10ddf3fd`
- Rotation Racket: `46ff1a1e325ee32a70b4144763ac97c8e53f3ba3385b5a60bcb1d4da7eaf0ac3`

## `public_eval_97d7923e` — cue-indexed vertical-bar rank

Built a second general canonical Racket rule and matched-input family:

- `rank_order=outer_to_inner` is canonical: measure each detached endpoint-color cue height `k`, order matching vertical bars by ascending top row, and recolor the kth bar interior.
- `rank_order=inner_to_outer` reverses the candidate order while preserving the same input-derived cue rank and visible inputs.
- Supports 2–6 demonstrations and four independently revealable, prefix-stable private queries, including a genuine 30x30 multi-color case.

Verification retained under `checks/public_eval_97d7923e/`:

- 12/12 current-source focused tests.
- All four supplied labelled pairs matched protected Racket.
- 320 audited episodes, 3,200 visible pairs, 2,240 declared-rival checks, 128 cross-setting query disagreements, 64 substantive 30x30 queries, 34 protected-label evaluations, 16 protected-rival evaluations, and 16 masked public views.
- Declared rivals: identity, opposite order, all bars, fixed first, fixed last, off-by-one, and column order.
- Source-bound counterfactual replaces cue-derived selection with fixed rank 1; protected replay changes 26 cells.

Exact hashes:

- Generator/sampler: `4fbd666bdead640ac7eb0df4430076d5a03f163537611e3ef19ebba8c7be6a98`
- Canonical Racket: `c73c163a01ac3f1dd1f3171ec12f2db80fc3e874c18a25eb5ae6caef285b802d`
- Reverse-rank Racket: `798366edd4accba3cbec20f7694079416de75b82c8e97c6c16c24f86194e7428`

## Reusable tooling

Each family includes a task-local `audit.py` that checks every demo count 2–6 across a bounded seed sweep, matched-input setting disagreement, finite shortcut rivals, protected Racket labels/rival refutations, public/private leakage, prefix stability, 30x30 stress cases, and hash-named single-query exports. The packet also retains `checks/tools/final_public_family_review.py`, a generic read-only verifier for exact preflight source closure, native-copy identity, focused receipts, public bytes, and causal replay status.

## Limits

The adversarial checks are bounded to declared rivals and generated seeds; they are not universal proofs of identifiability. The authoring preflights and witness replays do not grant native qualification, acceptance, or training admission. Both exact source closures must be registered and accepted independently by the owner.
