"""Independent audit geometry and demonstration-only survivor classification."""
import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parents[1] / "workspace/parametric"
spec = importlib.util.spec_from_file_location("rays_native_audit_test", HOME / "audit_native.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def grid(h, w, points, color=1):
    result = [[0] * w for _ in range(h)]
    for r, c in points:
        result[r][c] = color
    return result


def test_independent_literal_bounce_geometry():
    source = grid(9, 11, [(2, 6), (6, 3)], 5)
    expected = {
        (0,4),(1,5),(2,6),(3,7),(4,8),(5,9),(6,10),
        (3,0),(4,1),(5,2),(6,3),(7,4),(8,5),
        (1,3),(2,2),(3,1),(4,0),(7,9),(8,8),
        (2,1),(1,2),(0,3),(7,6),(6,7),(5,8),(4,9),(3,10),
    }
    assert audit.expected(source, "one_bounce") == grid(9,11,expected,5)
    assert source == grid(9,11,[(2,6),(6,3)],5)


def test_literal_corner_and_original_source_preservation():
    source = grid(7,7,[(2,2)],8)
    assert audit.expected(source,"one_bounce") == grid(7,7,[(i,i) for i in range(7)],8)
    assert audit.expected(source,"main_only","erase_original")[2][2] == 0
    assert audit.expected(source,"main_only","fixed_color_1")[2][2] == 8
    assert audit.expected(source,"main_only","fixed_color_1")[0][0] == 1


def test_detector_catches_synthetic_surviving_rival():
    official = {"train":[{"input":[[1]],"output":[[2]]}],
                "test":[{"input":[[3]],"output":[[4]]}]}
    result = audit.classify(official, [[[2]]], [[[9]]])
    assert result == {"status":"teaching_hole","demo_mismatches":[],"query_mismatches":[0]}
    assert audit.classify(official, [[[8]]], None)["status"] == "refuted_by_demos"
    assert audit.classify(official, [[[2]]], [[[4]]])["status"] == "survivor_agrees_all_queries"


def test_rival_names_are_bounded_and_meaningful():
    assert len(audit.rivals("both")) == 12
    assert len(audit.rivals("one_bounce")) == 17
    assert "first_3" in audit.rivals("one_bounce")
    assert "color_quota" in audit.rivals("one_bounce")
    assert "two_bounces" in audit.rivals("one_bounce")


def test_literal_extremal_shortcut_preserves_unlaunched_markers():
    row = grid(15,15,[(3,2),(3,6),(3,11)],4)
    column = grid(15,15,[(2,3),(6,3),(11,3)],4)
    for source, rival, marker, unpainted in (
            (row,"row_extremal",(3,6),(4,7)),
            (row,"row_column_extremal",(3,6),(4,7)),
            (column,"column_extremal",(6,3),(7,4)),
            (column,"row_column_extremal",(6,3),(7,4))):
        result = audit.expected(source,"main_only",rival)
        assert result[marker[0]][marker[1]] == 4
        assert result[unpainted[0]][unpainted[1]] == 0
        assert audit.expected(source,"main_only")[unpainted[0]][unpainted[1]] == 4
