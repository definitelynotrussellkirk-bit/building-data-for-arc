#!/usr/bin/env python3
"""Read-only triage of the completed repository run; writes only this checks directory."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

WORK = Path(__file__).resolve().parents[2]
REPO = WORK / 'repo'
OUT = Path(__file__).resolve().parent
ZIP = WORK.parent.parent / 'upload/SEND-THIS-ARCpuzzles-review(20261020-084231-1).zip'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

xml_path = WORK / 'checks/repository-tests.xml'
log_path = WORK / 'checks/repository-tests.log'
failures = []
for case in ET.fromstring(xml_path.read_bytes()).iter('testcase'):
    failure = case.find('failure')
    if failure is None:
        continue
    classname, name = case.attrib['classname'], case.attrib['name']
    if classname == 'tests.test_archival_reference':
        group = 'archival_expectations'
    elif name in ('test_resume_recipe_retains_policy_environment_and_schedule_copy',
                  'test_preflight_matches_isolated_test_interpreter'):
        group = 'interpreter_path_spelling'
    elif classname in ('tests.test_packet_racket_setup', 'tests.test_review_runtime'):
        group = 'protocol_expectations'
    elif classname == 'tests.test_server':
        group = 'socket_permission'
    elif classname in ('tests.test_check_audit_phase', 'tests.test_check_jobs',
                       'tests.test_check_resume', 'tests.test_check_signals'):
        group = 'process_table_mismatch'
    else:
        group = 'unclassified'
    failures.append({'node': classname.replace('.', '/') + '.py::' + name,
                     'group': group, 'message': failure.get('message'),
                     'traceback': failure.text or ''})
assert len(failures) == 19
write_json('failures.json', failures)

fixture_base = Path('/tmp/pytest-of-root/pytest-19')
fixture_paths = {
    'isolated_interpreter': fixture_base / 'test_preflight_matches_isolate0/ok/result.json',
    'policy_resume': fixture_base / 'test_resume_recipe_retains_pol0/policy recipe/result.json',
    'native_resume': fixture_base / 'test_native_battery_reuses_rec0/native/result.json',
    'committed_receipts': fixture_base / 'test_signal_before_child_exits0/between stages/result.json',
    'pinned_racket_resume': fixture_base / 'test_resume_recipe_restores_pi0/interrupted with pinned racket/result.json',
}
fixtures = {}
for name, path in fixture_paths.items():
    raw = path.read_bytes()
    data = json.loads(raw)
    keys = ('status', 'passed', 'settings', 'child_cleanup', 'resume_argv',
            'stdout', 'stderr', 'test_prerequisite_preflight')
    selected = {key: data[key] for key in keys if key in data}
    if name not in ('isolated_interpreter', 'policy_resume'):
        selected = {key: value for key, value in selected.items()
                    if key in ('status', 'passed', 'child_cleanup')}
    if 'test_prerequisite_preflight' in selected:
        selected['test_prerequisite_preflight'] = {
            key: value for key, value in selected['test_prerequisite_preflight'].items()
            if key in ('passed', 'test_interpreter', 'python_no_user_site', 'pythonpath',
                       'missing_dependencies', 'dependency_errors')}
    fixtures[name] = {'original_path': str(path), 'original_sha256': digest(raw),
                      'selected_evidence': selected}
write_json('fixture-evidence.json', fixtures)

# Recreate only the saved resume command's environment/interpreter prefix.
# The child reads settings; it does not run or resume a test/battery or write a checkpoint.
previous = json.loads(fixture_paths['policy_resume'].read_bytes())
resume = previous['resume_argv']
python_index = resume.index('-m') - 1
code = """from pathlib import Path
import hashlib,json,sys
from arcpuzzles import runtime
saved=Path(sys.argv[1]); old=json.loads(saved.read_bytes())
settings=runtime._check_settings(saved.parent)
for key in ('require_rotations_identifiable','compact_results','full_results','enumerate_schedule_period','schedule_seed'):
    if key in old['settings']:settings[key]=old['settings'][key]
settings['schedule_census_sha256']=hashlib.sha256((saved.parent/'checks/schedule-census-input.json').read_bytes()).hexdigest()
print(json.dumps({'previous_settings':old['settings'],'child_settings':settings,'differences':{key:{'previous':old['settings'].get(key),'child':settings.get(key)} for key in set(old['settings'])|set(settings) if old['settings'].get(key)!=settings.get(key)}},indent=2))
"""
argv = resume[:python_index + 1] + ['-c', code, str(fixture_paths['policy_resume'])]
started = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
child = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, timeout=20)
(OUT / 'settings-probe.log').write_text(child.stdout + child.stderr)
write_json('settings-probe-command.json', {'argv': argv, 'cwd': str(REPO),
    'started_utc': started, 'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'exit_code': child.returncode, 'scope': 'read-only settings comparison; no test rerun'})
assert child.returncode == 0, child.stderr
settings_probe = json.loads(child.stdout)
assert set(settings_probe['differences']) == {'python'}, settings_probe['differences']
write_json('settings-probe.json', settings_probe)

files = {row['node'].split('::')[0] for row in failures}
files.update(('src/arcpuzzles/runtime.py', 'src/arcpuzzles/check_jobs.py',
              'src/arcpuzzles/worker.py', 'src/arcpuzzles/server.py',
              'src/arcpuzzles/review_full_packet_files/setup_racket.py',
              'shared/tools/run_generator_battery.sh',
              'generators/defba1ab4f90/generator.py', 'generators/defba1ab4f90/notes.md',
              'generators/d982cffd80f8/generator.py', 'generators/d982cffd80f8/notes.md'))
source_checks = []
with zipfile.ZipFile(ZIP) as archive:
    for relative in sorted(files):
        current = (REPO / relative).read_bytes()
        original = archive.read('WORK/repo/' + relative)
        source_checks.append({'path': relative, 'sha256': digest(current),
                              'identical_to_uploaded_zip': current == original})
    for relative in ('run_with_racket.py', 'setup_racket.py'):
        current = (WORK / relative).read_bytes()
        original = archive.read('WORK/' + relative)
        source_checks.append({'path': '../' + relative, 'sha256': digest(current),
                              'identical_to_uploaded_zip': current == original})
assert all(row['identical_to_uploaded_zip'] for row in source_checks)
write_json('source-comparison.json', {'archive': str(ZIP), 'files': source_checks})

counts = Counter(row['group'] for row in failures)
footer = re.findall(r'^19 failed, .*$', log_path.read_text(), re.M)[-1]
summary = {
    'schema': 'repository-triage-v1',
    'repository_run': {'summary': footer, 'log_sha256': digest(log_path.read_bytes()),
                       'xml_sha256': digest(xml_path.read_bytes())},
    'failure_counts_by_measured_cause': dict(counts),
    'unclassified_failures': [row['node'] for row in failures if row['group'] == 'unclassified'],
    'unchanged_source_files': len(source_checks),
    'all_compared_sources_identical_to_uploaded_zip': True,
    'test_reruns': {'focused': {'receipt': 'focused-command.json', 'exit_code': 1, 'failed': 3},
                    'representative_signal': {'receipt': 'signal-command.json', 'exit_code': 1, 'failed': 1}},
    'read_only_diagnostics': ['inspect-causes-command.json', 'settings-probe-command.json'],
    'scope': 'No repository source edits or shared-tool repairs; no additional tests beyond the prior four reruns.'
}
write_json('summary.json', summary)

labels = {
    'archival_expectations': 'Historical archival expectations (2)',
    'process_table_mismatch': 'Process identity and cleanup verification (12)',
    'interpreter_path_spelling': 'Equivalent interpreter paths compared as raw strings (2)',
    'protocol_expectations': 'Stale exact protocol assertions (2)',
    'socket_permission': 'Socket creation denied (1)',
}
sections = ["# Repository-suite triage\n",
    f"**Completed run:** {footer}\n",
    "All 19 failure tracebacks were inspected. They are grouped below by observed cause; none remains unclassified at the immediate-failure level. This is bounded triage, not a successful repository-wide qualification. No repository source was modified.\n",
    "## Measured causes\n",
    "| Cause | Failed tests | Evidence |\n|---|---:|---|\n"
    "| Shipped archival expectations no longer match shipped generators | 2 | Full tracebacks, independent archival reruns, shipped generator notes |\n"
    "| `/proc` PIDs disagree with syscall PIDs | 12 | PID diagnostic; liveness tracebacks; retained cleanup receipts; representative foreground rerun |\n"
    "| Interpreter path spelling changes across child execution | 2 | Retained preflight/child traceback and exact saved-environment settings comparison |\n"
    "| Test expects an older diagnostic/command shape | 2 | Exact expected/actual tracebacks and unchanged implementation bytes |\n"
    "| Socket creation returns EPERM | 1 | Full server traceback before bind/listen |\n",
    "### Historical archival expectations\n",
    "`defba1ab4f90` expects historical hash `8b35cf5d…`; the shipped v2.0.0 sampler returns `b4ba8572…`, indexes `[0,1]`, and no rejections. Its shipped notes document replacement of the older v1.3.0 sampler. `d982cffd80f8` v3.0.0 accepts seed 17/index 0 with `self_check=[]`; the test still requires a rejection. Its shipped notes document repair of that validator. Both failures repeated in the focused run.\n",
    "### Process identity and cleanup verification\n",
    "The diagnostic measured syscall PID `6` and `/proc/self/stat` PID `55965`; `_process_table_supported()` returned false. Managed audit/jobs tests therefore receive `liveness_unknown`. All four foreground cases fail their fixture's direct `/proc/<pid>/stat` liveness assertion before sending the signal; one repeated in 0.29s. The live-child/PID-reuse cases likewise receive `liveness_unknown`. The native resume, committed-receipts, and pinned-Racket resume fixtures retain `session_empty=false` with `remaining_processes=null`; the runtime refuses to claim safe resume when process-table cleanup cannot be verified. This explains 12 failures without a timing-load assumption.\n",
    "### Interpreter path spelling\n",
    "The controller records `/WORK/repo/../.venv/bin/python`, while the child reports `/WORK/.venv/bin/python`. The prerequisite preflight actually passed: user site was disabled, inherited PYTHONPATH was absent, and pytest/NumPy/Pillow had no dependency errors. Its generated test then failed a raw `sys.executable` equality assertion. For the separate policy/schedule resume test, the read-only diagnostic recreated only the saved environment/interpreter prefix and recomputed settings: **the sole differing key was `python`**, with those equivalent spellings. The schedule hash and policy flags matched. No battery was rerun by this diagnostic.\n",
    "### Exact protocol assertions and socket restriction\n",
    "The packet-Racket test expects `Racket probe failed: unusable runtime`, but the unchanged implementation reports `Racket probe failed: returncode=1; stdout=''; stderr='unusable runtime'`; its mocked unusable runtime is rejected as intended. The review-runtime test expects a six-item battery command, while the unchanged implementation additionally supplies `--time-budget 310`. The HTTP test fails creating an AF_INET/SOCK_STREAM socket with `PermissionError: [Errno 1] Operation not permitted`, before binding or serving requests.\n",
    "## Complete failure mapping\n"]
for group, title in labels.items():
    sections.append(f"### {title}\n")
    sections.extend('- `' + row['node'] + '`\n' for row in failures if row['group'] == group)
    sections.append('\n')
sections.extend(["## Source and evidence binding\n",
    f"`source-comparison.json` verifies {len(source_checks)} relevant test, implementation, generator-note and wrapper files are byte-identical to the uploaded ZIP. It does not claim a fresh run of every test in a separate pristine extraction.\n",
    "- `../repository-tests.log` and `../repository-tests.xml`: completed run; hashes in `summary.json`.\n"
    "- `failures.json`: all 19 full failure records and cause assignments.\n"
    "- `fixture-evidence.json`: selected retained checkpoint/preflight fields, original paths and original-file hashes.\n"
    "- `focused-command.json`, `focused.log`: exact three-test rerun, exit 1.\n"
    "- `signal-command.json`, `signal.log`: exact one-case foreground rerun, exit 1.\n"
    "- `inspect_causes.py`, `inspect-causes-command.json`, `inspect-causes.log`: archival/PID/source diagnostic, exit 0.\n"
    "- `settings-probe-command.json`, `settings-probe.log`, `settings-probe.json`: exact read-only settings diagnostic, exit 0.\n"
    "- `summarize.py`, `summary-command.json`, `summary.json`: this reproducible triage collector and command receipt.\n",
    "## Limitations\n",
    "The broader repository suite remains failing. These measured causes are outside the assigned generator repair; no shared fixes or approval changes were made. The three skipped tests lack optional torch. The separately reported task-specific battery/tests and proposed parametric evidence are not upgraded or invalidated merely by this grouping. No load/timing explanation, universal runtime compatibility, or production approval is claimed.\n"])
(OUT / 'SUMMARY.md').write_text('\n'.join(sections))
print(json.dumps({'failure_groups': dict(counts), 'unchanged_files': len(source_checks),
                  'settings_difference_keys': list(settings_probe['differences']),
                  'summary': str(OUT / 'SUMMARY.md')}, indent=2))
