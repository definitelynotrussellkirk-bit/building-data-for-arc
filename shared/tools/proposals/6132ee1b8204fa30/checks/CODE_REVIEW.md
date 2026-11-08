# Final bounded code review — 0eb4eaa46003

## Disposition

No remaining important correctness or artifact-handling issue was found in the final reviewed source. The two substantive findings raised during this review are closed by the current changes. This is a bounded review of the generator, independent profile/reference probes, evidence compactor, profile-contract tests, and retained fixture. It does not establish completeness against all possible shortcuts.

Final generator SHA-256: `06b1f9325bd19b2f304de919efb6076fdfc4e4117c2e89f6eab2ec007933c093`.

Frozen baseline SHA-256: `f4b671a5803452cb71324aeb03fa529ca506afa04e022b3168f577ace69af1dc`.

The review did not consult final solve source, private labels, or solve-lane artifacts. No repository source was changed by this reviewer.

## Closed finding 1: candidate-only profile incidence

The first reviewed repair always placed the intended candidate at the intersection of a row-profile peer and a column-profile peer. Among non-anchor candidates, counting row-profile incidence plus column-profile incidence (including self twice) gave the target score 4 and both peers score 3. An optional extra distractor had a different area and score 2. Selecting the greatest score therefore ignored both anchors and succeeded on the entire previous generated support. Earliest component order resolved canonical ties in its favor, so the rival also fit the three canonical pairs.

The final generator alternates center selection with peripheral selection. In each even-index peripheral case, candidate incidence still prefers the center but the authoritative target is a leaf. Independently chosen anchors supply the selected leaf's two profiles. Exact target-copy anchors are excluded, which also defeats the compound strategy that first follows an exact candidate-copy anchor and otherwise falls back to incidence. Odd-index center cases retain the earlier 13-rival witness construction.

This closes the reproduced universal shortcut and its natural copy-then-incidence extension. The declared suite now has 15 rivals, of which 13 fit the canonical examples. Consecutive four-case windows contain both phases; holding out any one leaves both witness types among the three demonstrations.

## Closed finding 2: compactor destination symlinks

The former destination existence guard could miss dangling archive or sidecar symlinks and write through them. The corrected code rejects either destination when it is a symlink or already exists and creates both outputs exclusively (`xb` / `x`). Restore checks target boundaries and symlinks, leaves identical existing bytes unchanged, rejects conflicting contents, and creates a missing target exclusively.

The retained red tests reproduced the issue before correction. Inspection of the corrected guards and creation modes closes this finding. Concurrent hostile replacement of arbitrary parent directories is outside this local evidence utility's reviewed operating assumptions.

## Direct supplemental authority evidence

The directory `checks/anchor-role-counterfactuals/` contains:

- `fixture.json` and `input.json`: three authored inputs with exactly the same candidate pixels.
- `racket.json`: labels from the supported `arcpuzzles apply` command.
- `verify.py` and `comparison.json`: explicit-root/hash-aware independent checks.
- `commands.json`: complete argv, outer/payload cwd, environment, exit codes, source/rule/input binding, and command output for both runtime probes.

All three inputs pass the final generator's validator. Starting with the center-target scene, changing only the red anchor selects the row-profile leaf; changing only the blue anchor selects the column-profile leaf. The three actual Racket outputs differ and match both the authored target crops and the independent pixel/component mirror. Candidate incidence remains 4/3/3 throughout and fails on both leaf cases. No anchor exactly copies any candidate in this fixture.

These are hand-constructed validator-valid inputs, not claimed exact seeded production draws. Together they directly establish that a deterministic selector seeing only the fixed candidates cannot fit all three lawful anchor configurations.

Both runtime commands exited 0, with bytecode disabled and `TMPDIR=/dev/shm/arc-review-ecf4a172809240e3/tmp`.

Authority binding:

| Field | Value |
| --- | --- |
| Executed rule hash | `bb6e25e7de93` |
| Executed rule text SHA-256 | `f707d8410b23f3c8ff9920d430496243bf3cd188c809e9d251ff61e1823427b8` |
| Counterfactual input SHA-256 | `feefee37b7f4612ea3ee2fa78cb91b7833501d207710d23269251283ebe5bdf2` |

The parent separately reported the final accepted battery passing 12/12 stages, the lesson census passing 300 lessons and 1200 rotations, 36 isolated task tests passing, and four final reference inputs passing actual Racket. Those executions were not repeated by this reviewer and are distinct from the three direct authority inputs above.

## Remaining deliberate production restrictions

The generator remains a finite teaching curriculum. Targets have 4–10 connected cells and fit in a 4×3 or 3×4 catalog box; supported controls are grid height 10–24, width 14–24, shape size 4–10, 2–3 distractors, and palette size 4–6 including background. Separated placement cells and a three-candidate row/column-profile pattern constrain geometry, layout, and the types of ambiguity it emits. The main candidates and anchors have equal area and bbox dimensions; an optional additional distractor differs in area.

The final production generator deliberately excludes anchors that exactly copy the selected target. This restriction prevents the copy-then-incidence strategy from surviving the peripheral witness phase. Canonical scenes and other lawful exact target-copy anchor scenes remain accepted by the validator and unchanged Racket rule, but literal target-copy anchor scenes are not production draws.

The validator requires one blue anchor, one red anchor, and one uniquely matching target; the underlying rule also defines first-by-bbox behavior for multiple such components. The lesson guarantee concerns consecutive index windows, not arbitrary resampling. These limits should remain explicit and should not be described as complete support for every lawful input.

## Reviewed file hashes

| File below `generators/0eb4eaa46003/` | SHA-256 |
| --- | --- |
| `generator.py` | `06b1f9325bd19b2f304de919efb6076fdfc4e4117c2e89f6eab2ec007933c093` |
| `workspace/compact_evidence.py` | `bd70a68186dba3497a6f6457a9a356a7b8645c52b5dde32a4a4ff27996a43324` |
| `workspace/profile_probe.py` | `2aee64f9b56c9a59a4302f0a4906d3d15b90a80ef664fff968d0ec0cb171fe95` |
| `workspace/reference_probe.py` | `f7d975d791d7b1ee061d8cefdc828d2e2f889149553d52b08e4e41aac652f803` |
| `tests/test_profile_contract.py` | `016d443346371498d699e5816efc6659d9af0631fa597b5bb3f087044b692e03` |
| `counterexamples/equal_profiles_different_crops.json` | `68edd5fbf57e2a0f911d94232619575b0adc60e89b3c85f8f8d31262d4de380c` |
