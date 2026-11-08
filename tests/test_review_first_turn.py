"""Synthetic current-native-API regressions, with no Racket or assigned tasks.

The synthetic qualification/execution claims exist only in pytest's /tmp tree.
The real source inventory, native receipt parser, projection and verifier run;
no production validation function is replaced or disabled. These fixtures are
not evidence of Racket execution, label correctness or owner acceptance.
"""
from functools import partial
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from arcpuzzles import Catalog
from arcpuzzles import parametric_promotion as promotion


CHECKER_SOURCE = Path(__file__).resolve().parents[1] / "src/arcpuzzles/review_full_packet_files/check_first_turn.py"
SPEC = importlib.util.spec_from_file_location("_synthetic_first_turn_checker", CHECKER_SOURCE)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)
NATIVE = CHECKER.load_native()
TASK_ID = "aaaa00000001"


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


@pytest.fixture
def synthetic_qualification(tmp_path):
    """Small isolated source catalog adapted from current native test fixtures."""
    root = tmp_path / "synthetic-library"
    (root / "catalog").mkdir(parents=True)
    (root / "shared/data/canonical").mkdir(parents=True)
    home = root / "generators" / TASK_ID
    prototype = home / "workspace/parametric"
    prototype.mkdir(parents=True)
    code = "# synthetic source inventory fixture; never executed\n"
    program = "(rule! g)"
    (home / "generator.py").write_text(code)
    record = {"id": TASK_ID, "kind": "per_puzzle", "summary": "Synthetic API fixture",
              "sources": ["training"], "skills": ["reflection"], "difficulties": ["easy"],
              "primitives": ["flip-lr"], "aliases": [], "canonical_rows": 1,
              "generator": f"generators/{TASK_ID}/generator.py",
              "runtime_generator": f"puzzle_generators/per_puzzle/{TASK_ID}/generator.py",
              "version": "1.0.0", "rule_task_id": TASK_ID, "family": "synthetic",
              "split": "train", "parent_ids": [], "train_safety": "reviewed_safe",
              "mix_weight": 1.0, "semantic_veto": False, "veto_reason": "",
              "reviewed_generator_sha256": sha(code.encode()),
              "reviewed_rule_hash": sha(program.encode())[:12], "review_status": "",
              "health": "whitelist", "notes_count": 0}
    (root / "catalog/puzzles.jsonl").write_bytes(raw(record))
    (root / "catalog/runtime_files.json").write_bytes(raw([
        {"path": record["generator"], "target": record["runtime_generator"]}]))
    (root / "catalog/authority_files.json").write_bytes(raw({}))
    (root / "shared/data/canonical/puzzles.jsonl").write_bytes(raw({
        "task_id": TASK_ID, "program_solution": program,
        "train": [{"input": [[1]], "output": [[1]]}],
        "test": [{"input": [[2]], "output": [[2]]}]}))
    adapter = prototype / "adapter.py"
    adapter.write_text("# synthetic adapter inventory fixture; never executed\n")
    (prototype / "promotion.json").write_bytes(raw({
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": adapter.relative_to(root).as_posix(),
        "parameters": {"side": ["left", "right"]}, "default": {"side": "left"},
        "limits": {"demos": [2, 6], "queries": [1, 4]}}))
    catalog = Catalog(root)
    description = catalog.describe(TASK_ID)
    evidence = prototype / "evidence/manifest.json"
    evidence.parent.mkdir()
    evidence.write_bytes(raw({
        "task_id": TASK_ID, "generator_sha256": description["generator_sha256"],
        "canonical_rule_hash": description["rule_hash"],
        "verification_status": "reviewer_reported",
        "files": [{"path": adapter.relative_to(root).as_posix(),
                   "sha256": sha(adapter.read_bytes())}]}))
    contract, binding = promotion._ready(catalog, TASK_ID)
    jobs, episodes, checks = [], [], []
    for side in ("left", "right"):
        for seed in (0, 17):
            settings = {"side": side}
            program = "(rule! g)" if side == "left" else "(rule! (flip-lr g))"
            pairs = []
            for index in range(7):
                row = [seed // 10, seed % 10, index, 9]
                pairs.append({"input": [row], "output": [row if side == "left" else row[::-1]]})
            jobs.append({"settings": settings, "seed": seed, "demos": 3, "queries": 4})
            episodes.append({"task_id": TASK_ID, "settings": settings, "seed": seed,
                             "program": program, "program_sha256": sha(program.encode()),
                             "train": pairs[:3], "test": pairs[3:]})
            checks.append({"survivors": [settings], "label_count": 7})
    execution = {"episodes": episodes, "checks": checks,
                 "racket": {"backend": "racket", "protected": True},
                 "racket_evaluations": 28,
                 "synthetic_fixture_notice": "Claims only; no Racket executed."}
    programs = promotion._check_execution(execution, jobs, binding, contract)
    qualification = {"schema": promotion.QUALIFICATION, "status": "qualified",
                     "task_id": TASK_ID, "source_binding": binding, "contract": contract,
                     "jobs": jobs, "programs": programs,
                     "execution": {"path": "execution.json", "sha256": sha(raw(execution))},
                     "training_admitted": False,
                     "synthetic_fixture_notice": "Claims only; no Racket executed."}
    directory = tmp_path / "synthetic-qualification"
    directory.mkdir()
    path = directory / "qualification.json"
    path.write_bytes(raw(qualification))
    path.with_name("execution.json").write_bytes(raw(execution))
    # Bind the real native verifier to this isolated synthetic catalog.
    native = SimpleNamespace(**{name: getattr(NATIVE, name) for name in
                              ("SCHEMA", "LEGACY_SCHEMA", "public_view_bytes", "query_order")},
                             verify_export=partial(NATIVE.verify_export, library=root))
    return root, path, native


def test_shuffled_first_turn_follows_source_indices(synthetic_qualification, tmp_path):
    root, qualification, native = synthetic_qualification
    bundle = tmp_path / "synthetic-v2"
    NATIVE.export_qualified(qualification, bundle, library=root, presentation_seed=19)
    manifest = json.loads((bundle / "private/manifest.json").read_bytes())
    assert any(row["source_indices"][0] != 0 for row in manifest["episodes"])
    report = CHECKER.inspect_bundle(native, bundle)
    assert report["public_views_checked"] == 16
    assert report["first_turns_checked"] == 4
    assert report["invariance_checks"] == 24
    assert report["positive_controls"] == 4
    for case, mapping in zip(report["cases"], manifest["episodes"]):
        assert case["source_indices"] == mapping["source_indices"]
        assert case["first_source_query_index"] == mapping["source_indices"][0]
        assert case["first_view_sha256"] == mapping["view_ids"][0]


def test_native_legacy_projection_still_uses_source_order(synthetic_qualification, tmp_path):
    root, qualification, native = synthetic_qualification
    values = NATIVE._read_qualification(root, qualification)
    views, manifest = NATIVE._projection(*values, schema=NATIVE.LEGACY_SCHEMA)
    bundle = tmp_path / "synthetic-v1"
    (bundle / "public").mkdir(parents=True)
    (bundle / "private").mkdir()
    for identifier, payload in views.items():
        (bundle / "public" / f"{identifier}.json").write_bytes(payload)
    (bundle / "private/qualification.json").write_bytes(values[2])
    (bundle / "private/execution.json").write_bytes(values[3])
    (bundle / "private/manifest.json").write_bytes(NATIVE._raw(manifest))
    report = CHECKER.inspect_bundle(native, bundle)
    assert report["public_views_checked"] == 16
    assert all(case["source_indices"] == [0, 1, 2, 3] for case in report["cases"])
    assert all(case["first_source_query_index"] == 0 for case in report["cases"])


def test_shuffled_mapping_tampering_is_rejected_by_native_verification(synthetic_qualification, tmp_path):
    root, qualification, native = synthetic_qualification
    bundle = tmp_path / "synthetic-corrupt-v2"
    NATIVE.export_qualified(qualification, bundle, library=root, presentation_seed=19)
    path = bundle / "private/manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["episodes"][0]["source_indices"].reverse()
    path.write_bytes(NATIVE._raw(manifest))
    with pytest.raises(ValueError, match="manifest differs"):
        CHECKER.inspect_bundle(native, bundle)


@pytest.mark.parametrize('mapping', [[True, 1, 2, 3], [0, 0, 2, 3], [0, 1, 2], None])
def test_malformed_presentation_mapping_fails_closed(synthetic_qualification, tmp_path, mapping):
    root, qualification, native = synthetic_qualification
    bundle = tmp_path / 'malformed'
    NATIVE.export_qualified(qualification, bundle, library=root, presentation_seed=19)
    path = bundle / 'private/manifest.json'
    manifest = json.loads(path.read_bytes())
    manifest['episodes'][0]['source_indices'] = mapping
    path.write_bytes(NATIVE._raw(manifest))
    with pytest.raises(ValueError):
        CHECKER.inspect_bundle(native, bundle)


def test_relocated_cli_without_ambient_imports_preserves_private_report(synthetic_qualification, tmp_path):
    import os
    import shutil
    import subprocess
    import sys

    root, qualification, _ = synthetic_qualification
    home = CHECKER_SOURCE.parents[3]
    work = tmp_path / 'packet/WORK'
    repo = work / 'repo'
    shutil.copytree(root, repo)
    shutil.copytree(home / 'src', repo / 'src', ignore=shutil.ignore_patterns('__pycache__'))
    (repo / 'shared/runtime').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(home / 'shared/runtime/reviewer_support.py', repo / 'shared/runtime/reviewer_support.py')
    for name in ('check_first_turn.py', 'preview_public.py'):
        shutil.copyfile(CHECKER_SOURCE.with_name(name), work / name)
    checks = work / 'checks'
    checks.mkdir()
    q = json.loads(qualification.read_bytes())
    q['source_binding'] = promotion._ready(Catalog(repo), TASK_ID)[1]
    (checks / 'qualification.json').write_bytes(raw(q))
    shutil.copyfile(qualification.with_name('execution.json'), checks / 'execution.json')
    bundle = checks / 'preview'
    NATIVE.export_qualified(checks / 'qualification.json', bundle, library=repo, presentation_seed=19)
    env = dict(os.environ, PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH', None)
    argv = [sys.executable, '../check_first_turn.py', '--bundle', '../checks/preview',
            '--out', '../checks/first-turn.json']
    result = subprocess.run(argv, cwd=repo, env=env, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr + result.stdout
    report = json.loads((checks / 'first-turn.json').read_bytes())
    assert report['status'] == 'passed' and report['public_views_checked'] == 16
    assert report['racket_replayed'] is False and report['training_admitted'] is False
    assert report['owner_acceptance'] == 'not_performed'
    assert len(report['source_files']) == 4
    before = (checks / 'first-turn.json').read_bytes()
    duplicate = subprocess.run(argv, cwd=repo, env=env, capture_output=True, text=True, timeout=20)
    assert duplicate.returncode != 0
    assert (checks / 'first-turn.json').read_bytes() == before
    replaced = subprocess.run([*argv, '--replace', sha(before)], cwd=repo, env=env, capture_output=True, text=True, timeout=20)
    assert replaced.returncode == 0, replaced.stderr + replaced.stdout
    assert json.loads((checks / 'first-turn.json').read_bytes())['replaced_report_sha256'] == sha(before)


def test_guarded_report_replacement_preserves_changed_and_missing_evidence(tmp_path):
    target=tmp_path/'report.json';before=b'{"prior":"retained"}\n';target.write_bytes(before)
    expected=sha(before)
    with pytest.raises(ValueError,match='differs'):
        CHECKER.write_report(target,{'replacement':True},'0'*64)
    assert target.read_bytes()==before
    CHECKER.write_report(target,{'replacement':True},expected)
    assert json.loads(target.read_text())=={'replacement':True}
    current=target.read_bytes()
    with pytest.raises(ValueError,match='differs'):
        CHECKER.write_report(target,{'stale_writer':True},expected)
    assert target.read_bytes()==current
    with pytest.raises(ValueError,match='missing'):
        CHECKER.write_report(tmp_path/'missing.json',{},expected)
    link=tmp_path/'linked.json';link.symlink_to(target)
    with pytest.raises(ValueError,match='symlink'):
        CHECKER.write_report(link,{},sha(current))
