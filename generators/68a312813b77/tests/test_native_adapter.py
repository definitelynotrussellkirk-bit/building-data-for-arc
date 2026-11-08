"""Native boundary checks independent of the sampler's implementation tests."""
import hashlib
import importlib.util
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / "generators/68a312813b77"


def adapter():
    path = HOME / "workspace/parametric/adapter.py"
    assert path.is_file(), "native adapter is missing"
    spec = importlib.util.spec_from_file_location("native_68a312813b77_adapter_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_and_approved_generator_are_preserved_exactly():
    module = adapter()
    programs = {row["program_solution"] for row in Catalog(ROOT).get("68a312813b77")["variants"]}
    assert programs == {module.program({"completion": "bbox"})}
    assert module.program({"completion": "diagonal_gaps"}) not in programs
    assert hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest() == (
        "8e09a3589eab5c5413b7e2d6fb88f67f962dc6240ccdef01af31901f78419007"
    )


def test_generated_programs_match_native_selected_settings():
    module = adapter()
    for completion in ("bbox", "diagonal_gaps"):
        settings = {"completion": completion}
        episode = module.generate(17, settings, 3, 4)
        assert episode["program_solution"] == module.program(settings)
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
