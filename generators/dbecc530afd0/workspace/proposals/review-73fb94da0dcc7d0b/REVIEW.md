# Review — `dbecc530afd0`

Task/source: `dbecc530afd0`, production generator SHA-256 `4618d193dbd680fe48516a9f1968555824e50a7d1d35bb723bdd31f51ef17e02`.
Defect → repair: the isolated parameter writer exposed fixed episode ordinals, hard-coded 3 demonstrations/1 query, and treated rotations as query support; it now uses visible-content public IDs, independent bounded counts, and four simultaneous Racket-labelled queries.
Changed scope: `workspace/parametric/prototype.py`, its focused tests, README, and current task notes only.
Unchanged scope: production `generator.py`, canonical Racket source/rule hash, frozen fixtures, and existing dataset identities.
Retained result: two fixed-setting episodes, each with 3 shared demonstrations and 4 distinct queries; 8/8 canonical labels and all 8 query checks pass against the declared opposite-depth rival.
Tests: 32/32 focused parametric tests and 88/88 selected-task tests pass.
Adversarial pass: 704 sampler outputs across boundary counts passed production `self_check`; public/private identity mutations behaved as required.
Supplementary tickets: both bounded probes completed with no safety finding.
Remaining limit: finite two-setting/two-episode evidence against one declared rival; this does not approve the depth-2 variant or prove unique induction.
Status: complete; routine maintainer replay of the packaged commands remains required.

## Concrete repair

The retained prototype still varies only `inset_depth ∈ {1,2}`, with depth 1 byte-for-byte equal to the canonical Racket program and depth 2 produced by the existing guarded predicate substitution. One depth is fixed for the entire episode.

The writer now:

- validates demonstration and query counts independently as exact Python integers, `1..8` each and at most 12 total pairs;
- generates the requested number of distinct lawful inputs with an explicit bounded retry schedule;
- labels every demonstration and query through the episode's selected Racket program;
- checks every query against the opposite-depth rival using only the shared demonstrations;
- writes exact `reviewer_support.public_challenge_bytes(...)` as `public/challenge-<public_challenge_id>.json`;
- excludes seeds, settings, programs, private order, and query answers from public identity;
- sorts batch exports by public ID and rejects duplicate visible payloads instead of overwriting them.

The retained command uses 3 demonstrations and 4 queries per episode. The two public IDs are:

- `d864af5427a2f95bf72be911ad187d4343ae1a5b2033e4e5e82e48c8b64cff80`
- `f176dce826f0dae9d5eccd86b5d4bbc4d98c4653753653510011989c09ae23ea`

## Verification performed

TDD red evidence is retained at `checks/parametric/red-v2/pytest.log`: the new contract failed on the old prototype with 12 expected failures (missing count API and unsupported count arguments). After implementation:

- `checks/parametric/green-v2/pytest.log`: 32 focused tests passed.
- `checks/task-tests-v2/pytest.log`: all 88 selected-task tests passed.
- `checks/parametric/inset-depth-v2/report.json`: Racket 8.10; 8/8 canonical labels; two episodes; 6 demonstrations; 8 queries; 14 selected labels; 14 counterfactual labels; 14 unique episode inputs; zero query ambiguities against the declared rival.
- `checks/parametric/adversarial-v2/result.json`: 16 seeds × five boundary count cases, 704 lawful inputs, seven invalid count cases rejected, exact public bytes verified, private/query-answer mutations preserved IDs, and visible query-input mutations changed IDs.

The production generator hash remains `4618d193dbd680fe48516a9f1968555824e50a7d1d35bb723bdd31f51ef17e02`; the canonical ledger hash remains `a174c473ca475016e2af560afa98749537803bc6f856d3ea5195f94a21776eef`. The corrected prototype hash is `f6b2715cf36ea94beb900cd4f7132e67e7f39408d26437bf2ef5c39e0c91ddce`.

## Supplementary tickets

`ticket-3eb9054657e43e2a` checked the pinned `27b865c5f43a` `grid_h` API boundary: exact integer `8` produced a lawful 8×17 grid, while `True` was rejected with `TypeError`. Evidence: `checks/tickets/ticket-3eb9054657e43e2a/result.json`.

`ticket-cc146f928b12545b` checked the pinned `44d20451ce17` parameter evidence: both retained episodes have 3 demonstrations, 4 distinct queries, canonical visible-only public IDs, and query answers/private metadata excluded from identity. Evidence: `checks/tickets/ticket-cc146f928b12545b/result.json`.

Neither ticket produced a safety finding, so no `AUDIT.md` is included.

## Unresolved limits

This is an isolated prototype correction, not a production generator change. Evidence covers two consecutive seeds, the two declared inset-depth settings, and one opposite-depth rival. It does not enumerate all possible hypotheses, establish model behavior, approve the proposed variant, or admit any generated data to training.
