"""A failed executable rival must never masquerade as a teaching rejection."""
import importlib.util
from pathlib import Path


def audit_module():
    path = Path(__file__).resolve().parents[1] / 'workspace/audit_family.py'
    spec = importlib.util.spec_from_file_location('_jigsaw_audit_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_error_is_not_a_rejected_rival():
    module = audit_module()
    demos = [{'input': [[7]], 'output': [[5]]},
             {'input': [[7, 7]], 'output': [[5, 7]]}]
    result = module.teaching_result(demos, [{'error': 'bad program'}, {'output': [[7, 5]]}])
    assert result['status'] == 'runtime_failure'
    assert result['errors'] == [{'demo_index': 0, 'error': 'bad program'}]


def test_smallest_executed_disagreement_is_retained():
    module = audit_module()
    demos = [{'input': [[7, 7], [7, 7]], 'output': [[5, 7], [7, 7]]},
             {'input': [[7]], 'output': [[5]]}]
    result = module.teaching_result(demos, [{'output': [[7, 7], [7, 5]]}, {'output': [[7]]}])
    assert result['status'] == 'rejected_by_demo'
    assert result['demo_index'] == 1
    assert result['rival_output'] == [[7]]
    assert result['first_difference'] == {'position': [0, 0], 'expected': 5, 'actual': 7}


def test_matching_demos_are_not_claimed_to_identify_rule():
    module = audit_module()
    demos = [{'input': [[7]], 'output': [[5]]}]
    result = module.teaching_result(demos, [{'output': [[5]]}])
    assert result == {'status': 'survives_demonstrations'}


def test_grid_dimension_disagreement_is_reported_exactly():
    module = audit_module()
    assert module.first_difference([[5]], [[5, 7]]) == {
        'expected_shape': [1, 1], 'actual_shape': [1, 2]}
