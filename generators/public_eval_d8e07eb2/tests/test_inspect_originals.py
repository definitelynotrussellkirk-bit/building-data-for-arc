"""Behavioral checks for the all-pairs diagnostic; no label exceptions."""
from pathlib import Path
import importlib.util
import pytest


def tool():
    path=Path(__file__).resolve().parents[1]/'workspace/inspect_originals.py'
    assert path.is_file(), 'Implement the reusable all-pairs diagnostic'
    spec=importlib.util.spec_from_file_location('_test_original_inspector',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_diff_includes_changed_cells_and_shape_boundaries():
    m=tool()
    assert m.cell_differences([[1,2]],[[1,3]]) == [{'row':0,'col':1,'predicted':2,'supplied':3}]
    assert m.cell_differences([[1]],[[1,2],[3,4]]) == [
        {'row':0,'col':1,'predicted':None,'supplied':2},
        {'row':1,'col':0,'predicted':None,'supplied':3},
        {'row':1,'col':1,'predicted':None,'supplied':4}]


def test_source_format_accepts_digit_rows_without_coercing_cell_types():
    m=tool()
    assert m.original_grid(['012','987']) == [[0,1,2],[9,8,7]]
    assert m.original_grid([[0,1],[2,3]]) == [[0,1],[2,3]]
    for invalid in [[[True]],[[1.5]],[['1']],['1x'],[[-1]]]:
        with pytest.raises(ValueError):m.original_grid(invalid)


def test_renderer_marks_exact_discrepancy_without_mutating_grids():
    m=tool(); grid=[[1,2],[3,4]]
    svg=m.grid_svg(grid,{(0,1)})
    assert svg.count('class="changed"') == 1
    assert 'row 0, column 1, color 2' in svg
    assert grid == [[1,2],[3,4]]


def test_comparison_continues_after_failure_and_exception():
    m=tool(); calls=[]
    def apply(program,grid):
        calls.append(grid[0][0])
        if grid[0][0] == 2:raise RuntimeError('intentional fixture failure')
        return grid
    rows=[{'split':'train','index':i,'input':[[i]],'output':[[0]]} for i in range(3)]
    result=m.compare_pairs(rows,'program',apply)
    assert calls == [0,1,2]
    assert [x['status'] for x in result] == ['matched','mismatch','execution_error']
    assert result[1]['differences'] == [{'row':0,'col':0,'predicted':1,'supplied':0,'input':1}]
    assert 'intentional fixture failure' in result[2]['error']


def test_report_escapes_metadata_and_retains_explicit_limits():
    m=tool()
    report={'task_id':'<script>bad</script>','status':'blocked_original_labels',
            'matched':0,'labeled':1,'unlabelled_queries':0,
            'cases':[{'split':'train','index':0,'status':'execution_error','input':[[1]],
                      'supplied':[[2]],'error':'<script>bad</script>'}],
            'limits':'Diagnostic only; no qualification or acceptance.'}
    html=m.render_report(report)
    assert '<script>bad</script>' not in html
    assert '&lt;script&gt;bad&lt;/script&gt;' in html
    assert 'no qualification or acceptance' in html
