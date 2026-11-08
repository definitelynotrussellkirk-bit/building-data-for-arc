# Battery verdict reporter

Run from this directory using any Python 3 standard-library interpreter:

```bash
python3 summarize_battery.py ../../before/result.json
python3 summarize_battery.py ../../before/checks/e2fa7e7aee7c_before_battery_summary.json --json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s . -p 'test_*.py' -v
```

Accepts actual `generator_battery_summary/1` JSON or `arcpuzzles-check-v1` public result JSON with an embedded battery summary. It reads stage statuses and verifies recorded counts; malformed schemas, unknown statuses, empty stages, and count inconsistencies return exit 2. PASS and ADVISORY reports return exit 0; FAIL or INCOMPLETE reports return exit 1. Advisory exit 0 means findings are nonblocking, not that every stage is green. A raw battery summary contains no invocation exit code, so `completed_nonblocking_exit0` is null; the public result can supply it. The reporter describes recorded evidence and does not execute gates or revalidate evidence provenance.

## Verified baseline finding (F1)

The before public result exits 0 and embeds `passed_with_advisories`: PASS=10, ADVISORY=2, FAIL=0, UNFINISHED=0. Advisory stages are `profile_floor` and `semantic_gate`. Therefore `completed_nonblocking_exit0=true` and `every_stage_green=false`. The shell script correctly classifies and counts advisories in its JSON, but its final no-failure branch unconditionally prints `ALL 12 stages green`. This console claim overstates the evidence.

## Optional separate patch

`proposal.patch` changes only the final console verdict branch in `shared/tools/run_generator_battery.sh`: retain the all-green message for `all_green`, explicitly report nonblocking advisories for `passed_with_advisories`, and return nonzero for other aggregate verdicts. Stage policies, counts, and summary generation are unchanged. It was checked and applied only to a disposable copy, then passed `bash -n`. Original shared sources were not modified. Apply from the repository root only after reviewing the proposal:

```bash
git apply --check /absolute/path/to/proposal.patch
```

`verification.json` records test counts, commands, source identity, and compact baseline output. No full logs or battery artifacts are copied here.
