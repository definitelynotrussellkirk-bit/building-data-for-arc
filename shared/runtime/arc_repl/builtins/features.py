"""
Feature builtins — all features from FEATURE_REGISTRY.
"""

from .helpers import _make_feature_builtin

# Import features to trigger decorator registration
from .. import features as _features_module  # noqa: F401
from ..registry import FEATURE_REGISTRY


def register(env):
    """Register feature builtins into env."""

    # All features (auto-registered from FEATURE_REGISTRY)
    for name, entry in FEATURE_REGISTRY.items():
        env.define(name, _make_feature_builtin(entry.fn, entry.level))

    # Kebab-case aliases for features
    _feat_aliases = {
        'change-type': 'change_type', 'change-mask': 'change_mask',
        'color-frequency': 'color_frequency', 'border-pattern': 'border_pattern',
        'object-summary': 'object_summary', 'adjacency-graph': 'adjacency_graph',
        'color-roles': 'color_roles', 'input-invariant': 'input_invariant',
        'output-invariant': 'output_invariant', 'shape-change': 'shape_change',
        'object-count-change': 'object_count_change', 'consistent-mapping': 'consistent_mapping',
    }
    for alias, original in _feat_aliases.items():
        if original in FEATURE_REGISTRY:
            env.define(alias, _make_feature_builtin(FEATURE_REGISTRY[original].fn,
                                                     FEATURE_REGISTRY[original].level))
