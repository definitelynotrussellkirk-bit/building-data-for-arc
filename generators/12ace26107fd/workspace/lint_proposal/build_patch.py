"""Build an optional patch without modifying authoritative shared source."""
from pathlib import Path
import difflib
import hashlib
import json

here = Path(__file__).resolve().parent
repo = here.parents[3]
source = repo / "shared/tools/generator_defect_lint.py"
before = source.read_text()
after = before.replace(
    "def probe_selfcheck_minimal_impostors(module, inputs, bands, canonical_train=None):",
    "def probe_selfcheck_minimal_impostors(module, inputs, bands, canonical_train=None,\n"
    "                                     *, reference_label=None, rule_hash=None,\n"
    "                                     validation_notes=None):", 1)
start = after.index("def probe_selfcheck_minimal_impostors(")
end = after.index("\n\n# ----- machinery", start)
section = after[start:end]
section = section.replace("    accepted = Counter()", '''    # Optional semantic declaration, never a blanket waiver. A live canonical
    # label validates the claimed result, not semantic domain membership; the
    # task justification still needs maintainer review. Missing reference
    # execution or stale/malformed declarations retain the original finding.
    declarations = getattr(module, "LAWFUL_MINIMAL_PROBES", {})
    declaration_warnings = []
    specs = {}
    known = {"all_background", "full_one_color", "singleton", "solid_2x2", "short_line"}
    if not isinstance(declarations, dict):
        declaration_warnings.append("lawful-minimal-probes: expected a named mapping")
    else:
        for name, spec in declarations.items():
            valid = (
                isinstance(name, str) and name in known
                and isinstance(spec, dict)
                and set(spec) == {"justification", "rule_hash", "expected_output"}
                and isinstance(spec["justification"], str)
                and len(spec["justification"].strip()) >= 30
                and isinstance(rule_hash, str) and bool(rule_hash)
                and spec["rule_hash"] == rule_hash
                and _valid_arc_grid(spec["expected_output"])
                and callable(reference_label)
            )
            if valid:
                specs[name] = spec
            else:
                declaration_warnings.append(
                    f"lawful-minimal-probes: {name!r} not validated; require a known "
                    "kind, task justification, current rule hash, digit-grid expected "
                    "output, and live canonical reference")
    validated = Counter()
    accepted = Counter()''', 1)
section = section.replace("        used += 1\n        for name", '''        used += 1
        source_valid = False
        if specs:
            try:
                source_valid = _valid_arc_grid(_norm(reference_label(grid)))
            except Exception:
                pass
        for name''', 1)
section = section.replace("                accepted[name] += 1", '''                accepted[name] += 1
                if name in specs and source_valid:
                    try:
                        output = _norm(reference_label(mutation))
                        if (_valid_arc_grid(output)
                                and output == specs[name]["expected_output"]):
                            validated[name] += 1
                    except Exception:
                        pass''', 1)
section = section.replace("    canonical_lawful = _canonical_minimal_kinds(canonical_train)", '''    canonical_lawful = _canonical_minimal_kinds(canonical_train)
    reference_lawful = {name for name in specs
                       if accepted[name] and validated[name] == accepted[name]}
    for name in sorted(set(specs) - reference_lawful):
        if accepted[name]:
            declaration_warnings.append(
                f"lawful-minimal-probes: {name!r} live reference validation "
                f"passed {validated[name]}/{accepted[name]} accepted probes; "
                "original minimal-impostor finding retained")
    if reference_lawful and validation_notes is not None:
        validation_notes.append(
            f"lawful-minimal-probes: current canonical rule {rule_hash} validated "
            + ", ".join(f"{name} {validated[name]}/{accepted[name]}"
                        for name in sorted(reference_lawful))
            + "; domain membership remains a reviewed semantic declaration")''', 1)
section = section.replace("name not in canonical_lawful", "name not in canonical_lawful | reference_lawful", 1)
section = section.replace("    if not bad:\n        return []\n    return [", "    if not bad:\n        return declaration_warnings\n    return declaration_warnings + [", 1)
after = after[:start] + section + after[end:]
old = '''    warns += [
        {"issue": w, "count": 1}
        for w in probe_selfcheck_minimal_impostors(
            m, all_in, in_bands, canonical_train=canon.get(task_id)
        )
    ]'''
new = '''    minimal_reference = None
    minimal_rule_hash = None
    if rule_body is not None:
        from scripts.canonical_profile_gate import normalized_rule_hash
        minimal_rule_hash = normalized_rule_hash(rules[task_id])
        def minimal_reference(grid):
            bridge.define_grid("g", grid)
            return _norm(bridge.eval_text(rule_body))
    warns += [
        {"issue": w, "count": 1}
        for w in probe_selfcheck_minimal_impostors(
            m, all_in, in_bands, canonical_train=canon.get(task_id),
            reference_label=minimal_reference, rule_hash=minimal_rule_hash,
            validation_notes=notes,
        )
    ]'''
assert old in after
after = after.replace(old, new, 1)
compile(after, str(source), "exec")
patch = "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
    fromfile="a/shared/tools/generator_defect_lint.py",
    tofile="b/shared/tools/generator_defect_lint.py"))
(here / "generator_defect_lint.patch").write_text(patch)
identity = {"stock_sha256": hashlib.sha256(before.encode()).hexdigest(),
            "patched_sha256": hashlib.sha256(after.encode()).hexdigest(),
            "patch_sha256": hashlib.sha256(patch.encode()).hexdigest()}
(here / "source-hashes.json").write_text(json.dumps(identity, indent=2)+"\n")
print(json.dumps(identity, indent=2))
