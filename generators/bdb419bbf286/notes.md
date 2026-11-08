# Working notes: bdb419bbf286

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 — review-82eef943d118bfcd

- Repaired the historical last-marker ambiguity by adding later color-3/color-4 decoys to every generalized scene; their last-marker vector is required to produce a different clipped three-copy output from the canonical first-marker vector. Public fixtures remain exact.
- Preserved the canonical 4.0 rule; generator version is now 4.1.0 because generalized source bytes changed. The dedicated `marker_decoys` profile has an additional color-4 decoy, while all other generalized profiles have exactly two markers of each color.
- Added the native `repeat_rule` family: byte-exact `fixed_three` and sequential `to_boundary` (`select first source/markers and derive vector → repeat along that vector until no copy remains in bounds`).
- Construction was optimized after a self-review found exhaustive decoy-pair evaluation: deterministic shuffled early acceptance now preserves the lesson while making the prototype suite complete in about one second.
- Evidence: 16 focused tests; 32-seed bounded audit over 192 setting/count jobs and 1,472 pairs with zero declared-rival survivors and 1,472 last-marker failures; protected Racket authoring preflight for both settings at seeds 0 and 17; replayed wrong-intermediate witness; 16 public single-query views and 24 first-turn invariance checks; substantive 30×30 query.
- The catalog semantic veto remains intentionally unchanged. A source-bound authoring-only tooling patch is retained in `checks/tooling/repaired-semantic-veto-authoring.patch`; shared source was restored afterward. Owner source review must clear the veto before native qualification/acceptance. Training admission remains separate.

## Owner last-marker lesson repair

Protected owner replay confirms the historical seed0/medium/indices2..5
ambiguity. Returned v4.1.0 also had a supported three-demo/four-query hole at
seed414/medium/indices0..6: public_3, public_2, public_5 demonstrations fit the
last-marker rule, then generalized queries refute it. Distinct public inputs
mean ordinary duplicate rejection does not remove this witness.

Automatic draws now map a public-profile selection to an existing generalized
profile. All ordinary examples therefore run the discriminating later-marker
constructor. Explicit scene_profile public fixtures remain byte-exact, as do
all canonical and native Racket programs. Existing automatically selected
generalized examples keep their seeded draws. This changes only the ambiguous
automatic public branch; it introduces no new scene grammar or native setting.

The constructor accepts later markers only if their clipped three-copy union
differs from the first-marker union. Failure to construct such a scene raises;
it does not return a shortcut-equivalent example. Native generation independently
requires separation for both fixed-three and to-boundary programs. The current
owner evidence is bounded replay, not all-seed or all-rival proof. Original audit evidence remains retained. The last-marker A1 finding is now
explicitly resolved in the source-bound assessment in these notes; unrelated
audit findings remain unchanged.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ed3d39092c92c8c8:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `ec77658676ac993e0c84c4189a0847146c7d91bb734e25cdef581a9dedd4ff05`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Owner independently reproduced old seed0 witness and returned-source seed414 supported lesson failure. Fixed source cc624fcb44d66d0bf85e923b5ed0f75113209514e0d513181d9d68674e325443 routes every automatic draw through a discriminating later-marker constructor; exact public fixtures stay explicit. Protected owner replay verifies two supported lessons, five original labels, and fixed-downstream causal ablation. See generators/bdb419bbf286/evidence/owner-last-marker/fixed-protected-replay.json. This resolves only last-marker finding A1; no universal all-rival or seed-termination claim.

### Assessment or prior finding

## bdb419bbf286

**Finding A1 — reproduced teaching ambiguity (last-marker rival).** The canonical rule uses the first row-major color-3 and color-4 cells to define the translation vector. A plausible rival uses the last row-major 3 and 4 instead. With only one marker of each color, the rules agree.

A production-shaped four-pair sequence was found at seed `0`, sample indices `2..5`, difficulty `medium`, generator SHA `ec77658676ac993e0c84c4189a0847146c7d91bb734e25cdef581a9dedd4ff05`. Its profiles are `axis_aligned`, `public_5`, `clipped_copies`, and `marker_decoys`. Treating the first three pairs as demonstrations and the fourth as query, the last-marker rival matches the selected Racket authority on all 3/3 demonstrations and disagrees on the query. Thus individually correct labels do not make this lesson identifiable.

The exact four generated inputs pass the task validator and belong to the documented scene-profile domain. I obtained all four outputs through the supported `arcpuzzles apply` command; executed rule hash `6669efb7af1c` matches the catalog. `checks/audit/bdb419bbf286/counterexample.json` binds the generator/rule hashes, seed, profiles, command, actual query output, and rival output; `input.json`, `racket.json`, and `rival-last-marker.json` retain full grids.

**Suggested repair (not applied).** Declare this rival and require at least one `marker_decoys` demonstration whenever another pair may be the query, or make every default example include later decoys that do not alter the first-marker vector. Then run a rotated lesson census.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-ed3d39092c92c8c8-v0001/audit_assets.json), manifest SHA-256 `539f0c4b425d77f0a2dbcb10a695bf791db7bdd931f12a380130f587b32f9db8`.
<!-- arcpuzzles-current-audit-assessment:end -->
