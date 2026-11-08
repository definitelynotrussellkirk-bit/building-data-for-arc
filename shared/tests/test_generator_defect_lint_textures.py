from __future__ import annotations

from types import SimpleNamespace

from scripts.generator_defect_lint import (
    probe_texture_domain_overlap,
    probe_texture_overrides,
)


def _module(*, exempt: bool) -> SimpleNamespace:
    def generate(seed, sample_index, *, difficulty=None, texture=None):
        del sample_index, difficulty
        color = 2 if texture == "edge" else 1
        return [[color, seed % 10], [0, 0]]

    def self_check(grid, *, difficulty=None):
        del grid, difficulty
        return []

    fields = {
        "AXES": {"texture": {"type": "str", "valid": "plain"}},
        "DEGENERATE_TEXTURES": ("edge",),
        "HELPFUL_TEXTURES": (),
        "generate": generate,
        "self_check": self_check,
    }
    if exempt:
        fields["LAWFUL_DEGENERATE_TEXTURES"] = ("edge",)
    return SimpleNamespace(**fields)


def test_accepted_degenerate_texture_is_warning_without_exemption() -> None:
    warnings, notes = probe_texture_overrides(_module(exempt=False))

    assert any("LAWFUL_DEGENERATE_TEXTURES" in item for item in warnings)
    assert not notes


def test_lawful_degenerate_texture_can_be_explicitly_exempted() -> None:
    warnings, notes = probe_texture_overrides(_module(exempt=True))

    assert not warnings
    assert any("explicitly exempted" in item for item in notes)


def test_valid_texture_domain_cannot_include_negative_fixture() -> None:
    module = _module(exempt=False)
    module.AXES = {"texture": {"type": "str", "valid": "plain|edge"}}

    errors = probe_texture_domain_overlap(module)

    assert len(errors) == 1
    assert "texture-domain-overlap" in errors[0]
    assert "edge" in errors[0]


def test_lawful_edge_texture_may_remain_in_valid_domain() -> None:
    module = _module(exempt=True)
    module.AXES = {"texture": {"type": "str", "valid": ["plain", "edge"]}}

    assert probe_texture_domain_overlap(module) == []


def test_negative_fixture_labels_are_not_assumed_to_be_texture_overrides() -> None:
    module = _module(exempt=False)
    module.AXES = {}

    warnings, notes = probe_texture_overrides(module)

    assert warnings == []
    assert notes == []
