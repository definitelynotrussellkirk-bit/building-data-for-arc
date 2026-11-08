"""
Registry infrastructure — transforms and features carry metadata for help/discovery.

Each entry has: name, category, signature, description, example.
The help system reads this at runtime.
"""

from dataclasses import dataclass, field


@dataclass
class TransformEntry:
    fn: callable
    name: str
    category: str       # geometric, color, spatial, object, structural, fill, pattern, conditional
    signature: str       # "recolor <grid> <src> <dst>"
    description: str     # one line
    example: str = ""    # "transform! recolor @1 8 7"
    accepts_mask: bool = False

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)


@dataclass
class FeatureEntry:
    fn: callable
    name: str
    level: str          # "pair", "grid", "task"
    signature: str
    description: str
    example: str = ""

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)


# Global registries
TRANSFORM_REGISTRY: dict[str, TransformEntry] = {}
FEATURE_REGISTRY: dict[str, FeatureEntry] = {}


def register_transform(category, signature, description, example="", accepts_mask=False):
    """Decorator to register a transform with metadata."""
    def decorator(fn):
        TRANSFORM_REGISTRY[fn.__name__] = TransformEntry(
            fn=fn, name=fn.__name__, category=category,
            signature=signature, description=description,
            example=example, accepts_mask=accepts_mask,
        )
        return fn
    return decorator


def register_feature(level, signature, description, example=""):
    """Decorator to register a feature with metadata."""
    def decorator(fn):
        FEATURE_REGISTRY[fn.__name__] = FeatureEntry(
            fn=fn, name=fn.__name__, level=level,
            signature=signature, description=description,
            example=example,
        )
        return fn
    return decorator


# ============================================================
# Help rendering
# ============================================================

def _canonical_name(name):
    """Return the canonical kebab-case form of a name."""
    return name.replace("_", "-")


def _canonical_signature(sig):
    """Convert signature to kebab-case form."""
    return sig.replace("_", "-")


def list_transforms(category=None, canonical=True):
    """List transforms, optionally filtered by category.

    If canonical=True (default), only shows kebab-case names and deduplicates
    entries that are registered under both snake_case and kebab-case.
    """
    entries = TRANSFORM_REGISTRY.values()
    if category:
        entries = [e for e in entries if e.category == category]
    by_cat = {}
    seen = set()
    for e in entries:
        canon = _canonical_name(e.name)
        if canonical and canon in seen:
            continue
        seen.add(canon)
        by_cat.setdefault(e.category, []).append(e)

    lines = []
    for cat in sorted(by_cat):
        lines.append(f"=== TRANSFORMS: {cat} ({len(by_cat[cat])}) ===")
        for e in sorted(by_cat[cat], key=lambda x: _canonical_name(x.name)):
            if canonical:
                lines.append(f"  {_canonical_signature(e.signature):<45s} {e.description}")
            else:
                lines.append(f"  {e.signature:<45s} {e.description}")
    return "\n".join(lines)


def list_features(level=None, canonical=True):
    """List features, optionally filtered by level.

    If canonical=True (default), only shows kebab-case names and deduplicates.
    """
    entries = FEATURE_REGISTRY.values()
    if level:
        entries = [e for e in entries if e.level == level]
    by_level = {}
    seen = set()
    for e in entries:
        canon = _canonical_name(e.name)
        if canonical and canon in seen:
            continue
        seen.add(canon)
        by_level.setdefault(e.level, []).append(e)

    lines = []
    for lev in ["pair", "grid", "task"]:
        if lev not in by_level:
            continue
        lines.append(f"=== FEATURES: {lev}-level ({len(by_level[lev])}) ===")
        for e in sorted(by_level[lev], key=lambda x: _canonical_name(x.name)):
            if canonical:
                lines.append(f"  {_canonical_signature(e.signature):<45s} {e.description}")
            else:
                lines.append(f"  {e.signature:<45s} {e.description}")
    return "\n".join(lines)


def help_for(name):
    """Get detailed help for a transform or feature.

    Looks up by both snake_case and kebab-case, but always displays
    the canonical kebab-case form.
    """
    # Try snake_case lookup, then kebab->snake conversion
    entry = TRANSFORM_REGISTRY.get(name) or TRANSFORM_REGISTRY.get(name.replace("-", "_"))
    if entry:
        canon = _canonical_name(entry.name)
        sig = _canonical_signature(entry.signature)
        example = _canonical_signature(entry.example) if entry.example else ""
        lines = [canon, f"  {sig}", f"  {entry.description}", f"  Category: {entry.category}"]
        if example:
            lines.append(f"  Example: {example}")
        return "\n".join(lines)

    entry = FEATURE_REGISTRY.get(name) or FEATURE_REGISTRY.get(name.replace("-", "_"))
    if entry:
        canon = _canonical_name(entry.name)
        sig = _canonical_signature(entry.signature)
        example = _canonical_signature(entry.example) if entry.example else ""
        lines = [canon, f"  {sig}", f"  {entry.description}", f"  Level: {entry.level}"]
        if example:
            lines.append(f"  Example: {example}")
        return "\n".join(lines)

    return f"Unknown command: {name}. Try list! to see all."


def list_categories():
    """List all transform categories and feature levels."""
    t_cats = sorted(set(e.category for e in TRANSFORM_REGISTRY.values()))
    f_levels = sorted(set(e.level for e in FEATURE_REGISTRY.values()))
    lines = [f"Transform categories: {', '.join(t_cats)}",
             f"Feature levels: {', '.join(f_levels)}"]
    return "\n".join(lines)
