"""Optional shared preparation reporter proposal; no live-task execution."""
from __future__ import annotations

def instrument_source(source: str) -> str:
    """Generate a small optional reporter patch, refusing source-shape drift."""
    substitutions = [
        ('    try:\n        config["n_train"] = _demonstration_count(source_bytes)',
         '    preparation_stage = "demonstration_contract"\n    try:\n        config["n_train"] = _demonstration_count(source_bytes)\n        preparation_stage = "episode_materialization"'),
        ('        _validate_public(public)\n',
         '        preparation_stage = "public_validation"\n        _validate_public(public)\n        preparation_stage = "artifact_persistence"\n'),
        ('        base.update({"status": "blocked", "stopping_reason": "Episode generation blocked: " + type(exc).__name__})',
         '        failure_code = {"demonstration_contract": "invalid_demonstration_contract",\n'
         '                        "episode_materialization": "episode_materialization_failed",\n'
         '                        "public_validation": "invalid_public_episode",\n'
         '                        "artifact_persistence": "artifact_persistence_failed"}[preparation_stage]\n'
         '        base.update({"status": "blocked", "stopping_reason": "Episode generation blocked: " + type(exc).__name__,\n'
         '                     "preparation_stage": preparation_stage, "failure_code": failure_code})'),
        ('        "stopping_reason", "final_notes_path", "final_notes_sha256",',
         '        "stopping_reason", "preparation_stage", "failure_code", "final_notes_path", "final_notes_sha256",'),
    ]
    for old, new in substitutions:
        if source.count(old) != 1:
            raise ValueError('Reporter proposal does not match this generic source version')
        source = source.replace(old, new)
    return source



def classify_private_error(error: str, exception_type: str) -> dict:
    """Return fixed safe categories only; never return source/error fragments."""
    code = 'private_detail_suppressed'
    if exception_type == 'ValueError' and error.startswith('malformed node or string'):
        code = 'nonliteral_demonstration_declaration'
    elif error == 'EXAMPLES_NEEDED must be a literal integer in 1..32':
        code = 'invalid_demonstration_declaration'
    elif error == 'Mapped runtime receipt reader conflicts with the installed reader':
        code = 'runtime_receipt_reader_conflict'
    node_class = None
    if code == 'nonliteral_demonstration_declaration':
        for candidate in ('BinOp', 'Name', 'Call', 'Attribute', 'Subscript', 'IfExp', 'UnaryOp', 'Constant'):
            if '<ast.' + candidate + ' object at ' in error:
                node_class = candidate
                break
    return {'safe_code': code, 'ast_node_class': node_class,
            'raw_private_detail_emitted': False}
