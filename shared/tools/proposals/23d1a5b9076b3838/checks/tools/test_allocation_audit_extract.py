import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).with_name('allocation_audit_extract.py')


def load_module():
    spec = importlib.util.spec_from_file_location('allocation_audit_extract', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_assignment_seed_reproduces_required_sample():
    module = load_module()
    seed = 'fa92ffbfd8368c880d209c78bf5533415e01b485f3dfed29d4f239e0f67fb4ad'
    report = module.build_report(ROOT, seed, sample_size=3)
    assert report['sampled_ids'] == ['1520a56aa617', '26b41ff6047f', '5875afa30211']


def test_report_separates_authoring_probability_from_dataset_weight():
    module = load_module()
    seed = 'fa92ffbfd8368c880d209c78bf5533415e01b485f3dfed29d4f239e0f67fb4ad'
    report = module.build_report(ROOT, seed, sample_size=3)
    assert report['authoring_policy']['normal_pool_count'] == 252
    assert report['authoring_policy']['evaluation_focus_probability'] == {'numerator': 1, 'denominator': 10}
    assert all(row['in_normal_authoring_pool'] is False for row in report['sample'])
    assert all(row['dataset_sampling_weight'] == 1.0 for row in report['sample'])


def test_retained_unresolved_audit_is_visible():
    module = load_module()
    seed = 'fa92ffbfd8368c880d209c78bf5533415e01b485f3dfed29d4f239e0f67fb4ad'
    report = module.build_report(ROOT, seed, sample_size=3)
    row = next(row for row in report['sample'] if row['task_id'] == '5875afa30211')
    assert row['retained_audits'][0]['resolution'] == 'unresolved'
    assert 'exact-axis contract' in row['retained_audits'][0]['text']


def test_output_is_json_serializable_and_paths_are_relative():
    module = load_module()
    seed = 'fa92ffbfd8368c880d209c78bf5533415e01b485f3dfed29d4f239e0f67fb4ad'
    report = module.build_report(ROOT, seed, sample_size=3)
    json.dumps(report, sort_keys=True)
    for row in report['sample']:
        for path in row['evidence_paths']:
            assert not Path(path).is_absolute()
