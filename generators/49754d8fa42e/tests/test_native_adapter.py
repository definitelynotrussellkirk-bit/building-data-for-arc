"""Native contract and exact canonical authority regression."""
import hashlib
import importlib.util
from pathlib import Path


HOME = Path(__file__).resolve().parents[1]


def adapter():
    path = HOME / "workspace/parametric/adapter.py"
    assert path.is_file(), "native adapter is missing"
    spec = importlib.util.spec_from_file_location("native_mode_glyph_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_default_preserves_exact_catalog_and_production_bytes():
    from arcpuzzles import Catalog
    m = adapter()
    programs = {v["program_solution"] for v in Catalog(".").get("49754d8fa42e")["variants"]}
    assert programs == {m.program({"orientation": "canonical"})}
    assert m.program({"orientation": "modal_components"}) != next(iter(programs))
    assert hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest() == "99216a3011a7653571ee5539b6782bc5403d40f207bfab945fadeefdf02af6c6"


def test_native_generated_program_exactly_matches_selected_rule():
    m = adapter()
    for mode in ("canonical", "modal_components"):
        settings = {"orientation": mode}
        episode = m.generate(17, settings, 3, 4)
        assert episode["program_solution"] == m.program(settings)
        assert len(episode["train"]) == 3 and len(episode["test"]) == 4
