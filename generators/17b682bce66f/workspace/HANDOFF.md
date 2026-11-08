# Handoff — review-ef189c36f23d1a7e

## State that must not be rediscovered

Task `17b682bce66f`, final generator SHA-256
`1be83f9295055acdf8e86a1ce2258ad7c70891978251b31438426049ae953876`, version 3.1.0.
Racket authority unchanged. The old source had exactly 199 inputs and ten
normalized layouts. The repair retains all ten witnesses and adds procedural
clouds, references and layouts. Final battery: 12 green; task tests: 13 passed
plus 8 subtests; actual authority parity: 271 comparisons / 147 unique inputs.

Do not count same forced-profile seeds across bands as independent. Do not claim
a Qwen improvement from these support measurements. The required solve is
finished with earlier exposure declared, 3/3 visible matches and masked accuracy
unknown. Its public ambiguity probe finds multiple visible-consistent policies
that disagree on query 2. Do not consult labels to repair that recorded episode.

The whole repository still has T1, an unrelated shared test-fixture import
failure: 165 passed, 1 failed. Its proposed fix was verified only in an isolated
copy, where all 21 tests in the affected file pass. Two audit-only sources are
unchanged; read `AUDIT.md` rather than conflating them with this patch.

## Apply and inspect

Use the returned patch only against the matching packet/repository baseline.
The return is a delta with reports/checks/solve artifacts, not a self-contained
repository. `INTAKE.json` and `RESULTS.json` bind source identities, commands and
hashes. No installed Racket environment or staged runtime is included.

Commands below are from the **original packet root after applying the patch**.
Paths beginning with `repo/` are relative to that root. New examples use distinct
output names; probe reports are exclusive and must not overwrite prior evidence.

```sh
python3 setup_racket.py
export RACKET_PATH="$PWD/.review/racket-runtime/racket/bin/racket"
export PATH="$(dirname "$RACKET_PATH"):$PATH"
PROBE=repo/generators/17b682bce66f/workspace/review_probe.py
python3 "$PROBE" stage --runtime .review/verify_runtime --out checks/verify_stage.json
python3 -m pytest -q repo/generators/17b682bce66f/tests
(cd .review/verify_runtime && python3 -m pytest -q \
  tests/test_generator_17b682bce66f.py tests/test_review_probe.py)
python3 "$PROBE" census --runtime .review/verify_runtime \
  --samples 600 --seed-start 0 --assert-novelty --out checks/verify_census.json
python3 "$PROBE" census --runtime .review/verify_runtime \
  --profile procedural --samples 2000 --seed-start 10000 \
  --assert-novelty --out checks/verify_stress.json
python3 "$PROBE" parity --runtime .review/verify_runtime \
  --samples 30 --profile-samples 16 --out checks/verify_parity.json
```

`--profile` is used **only by census**. Parity enumerates every declared profile
using `--profile-samples`; it does not honor `--profile`. Census executes Python
and self-checks only. Parity needs the actual Racket runtime and invokes the
canonical authority; it is not mirror self-agreement. Its `--task-id` permits use
with the audit targets. Reports contain actual argv, hashes, per-seed metadata,
failures and elapsed times. The novelty cutoff is calibrated only for this task.

The shared wrapper runs its child from **repo**, unlike the direct commands above:

```sh
python3 run_with_racket.py python3 -m arcpuzzles check 17b682bce66f \
  --battery --timeout 4000 --phase after --out ../checks/verify_battery
python3 run_with_racket.py python3 -m arcpuzzles check 17b682bce66f \
  --stage lint --phase after --out ../checks/verify_lint
python3 run_with_racket.py python3 -m pytest -q
```

The last command is expected to expose T1 on the incoming shared test source,
not to give a fully green repository suite. Read the complete output.

## Reproduce the before baseline without reverting shared work

The original packet's immutable snapshot is under `.review/baseline/repo/`.
Create a second runtime, then replace only its selected generator with that saved
source. This does not change the source checkout or immutable snapshot:

```sh
python3 "$PROBE" stage --runtime .review/verify_before --out checks/verify_before_stage.json
cp .review/baseline/repo/generators/17b682bce66f/generator.py \
  .review/verify_before/puzzle_generators/per_puzzle/17b682bce66f/generator.py
python3 "$PROBE" census --runtime .review/verify_before \
  --samples 600 --seed-start 0 --assert-novelty --out checks/verify_before_census.json
# The preceding command intentionally exits 1: the baseline fails the new gate.
python3 repo/generators/17b682bce66f/workspace/fixed_bank_capacity.py \
  --runtime .review/verify_before --out checks/verify_before_capacity.json
```

The helper census hashes the **loaded source**, so the replaced baseline is
identified correctly. The staging receipt predates this explicit source swap;
do not treat that receipt alone as authority for the loaded generator. A
maintainer can alternatively stage from an untouched baseline checkout. The
capacity script measures only the fixed bank; 199 is the whole support only for
the old bank-only generator, not version 3.1.0.

## Reproduce audit-only and fixture findings

The audit helper expects the following exact runtime names. On a fresh packet:

```sh
python3 "$PROBE" stage --task-id f2dbde875127 \
  --runtime .review/audit_frames_runtime --out checks/replay_frames_stage.json
python3 "$PROBE" stage --task-id 5f9a2df57599 \
  --runtime .review/audit_walls_runtime --out checks/replay_walls_stage.json
python3 repo/generators/17b682bce66f/workspace/audit_findings.py
python3 "$PROBE" parity --task-id 5f9a2df57599 \
  --runtime .review/audit_walls_runtime --samples 20 --profile-samples 2 \
  --out checks/replay_walls_parity.json
python3 repo/generators/17b682bce66f/workspace/verify_fixture_repair.py
```

`audit_findings.py` and `verify_fixture_repair.py` write fixed, exclusive report
paths `checks/audit_findings.json` and `checks/fixture_import_repair.json`.
On a rerun, first archive the old reports under new names, or use a clean working
copy; do not delete evidence. Both helpers leave audited/shared source untouched.
The fixture report includes the proposed unified diff and both exit codes.

## Next owner actions

Review the source diff and rerun the staged checks before accepting the generator.
Integrate T1's verified fixture proposal separately under the shared-code owner's
scope. Address the frame-task audit findings in that task's own assignment.
For lesson construction, add a collision-disambiguating demonstration when a
query needs that behavior; the public solve probe is a counterexample to assuming
that visible 3/3 implies an identified rule. Leave recorded solve artifacts intact.
