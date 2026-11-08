"""Retain the current sampler while exposing the reviewer's endpoint rival."""
from reviewer_support import find_root, load_selected_generator

gen, _, _ = load_selected_generator("3a4b67ab16ff", root=find_root(__file__))

def test_distributed_extrema_has_an_executable_endpoint_rival_binding():
    name = "distributed_extrema_refutes_endpoint_only_bbox"
    assert gen.WITNESS_RIVALS[name] == ["endpoint_only_bbox"]
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(91, 3, difficulty=band, scene_profile="distributed_extrema")
        assert gen.SEMANTIC_WITNESSES[name](grid)
        assert gen.SEMANTIC_RIVALS["endpoint_only_bbox"](grid) != gen.rule_mirror(grid)
