"""Regression for an actual ambiguous cyclic query on an intermediate repair."""
import importlib.util
from pathlib import Path

import pytest

# pytest's portable --import-mode=importlib does not add this directory to
# sys.path. Bind the oracle to the test's exact sibling in the current tree.
_contract_path = Path(__file__).resolve().with_name("test_generator_contract.py")
_contract_spec = importlib.util.spec_from_file_location(
    "c5a80b7a3acc_lesson_contract_oracle", _contract_path)
_contract = importlib.util.module_from_spec(_contract_spec)
_contract_spec.loader.exec_module(_contract)
gen, set_output = _contract.gen, _contract.set_output


@pytest.mark.parametrize("seed,band", [(259, "hard"), (4702, "easy")])
def test_all_cyclic_query_choices_refute_declared_rivals(seed, band):
    # Intermediate source 416e3912... allowed green-minus-red to fit all five
    # demonstrations for query #2 at seed259. Labels were independently
    # checked by canonical Racket; this test uses the pixel-derived test oracle.
    pairs = [{"input": gen.generate(seed, index, difficulty=band)}
             for index in range(6)]
    for pair in pairs:
        pair["output"] = set_output(pair["input"])
    for query_index in range(6):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                f"seed={seed}, band={band}, query={query_index}: "
                f"{name} survives all five demonstrations"
            )
