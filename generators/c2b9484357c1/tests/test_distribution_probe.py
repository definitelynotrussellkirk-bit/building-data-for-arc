from pathlib import Path
import importlib.util


def test_shape_fingerprint_ignores_only_declared_cosmetics():
    path = Path(__file__).resolve().parents[1] / 'workspace/measure_distribution.py'
    assert path.is_file(), 'distribution probe missing'
    spec = importlib.util.spec_from_file_location('distribution_probe', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    frame = {(r, c) for r in range(4) for c in range(5)
             if r in (0, 3) or c in (0, 4)}
    changed = frame | {(1, 2)}
    shifted_rotated = {(12-c, 7+r) for r, c in frame}
    assert mod.shape_fingerprint([frame]) == mod.shape_fingerprint([shifted_rotated])
    assert mod.shape_fingerprint([frame]) != mod.shape_fingerprint([changed])
    assert mod.shape_fingerprint([frame]) != mod.shape_fingerprint([frame, frame])
