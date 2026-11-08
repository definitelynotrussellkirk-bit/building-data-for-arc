"""Public API for the additive ARC-Racket v2 core compiler."""

from .compiler import CompilationResult, CostLimits, SourceMapEntry, V2CompileError, compile_source
from .migrate import MigrationResult, UnsupportedMigration, migrate_legacy_source
from .signatures import CONSTANTS, SIGNATURES, constant_rows, signature_rows

__all__ = [
    "CompilationResult",
    "CostLimits",
    "V2CompileError",
    "compile_source",
    "MigrationResult",
    "UnsupportedMigration",
    "migrate_legacy_source",
    "CONSTANTS",
    "SIGNATURES",
    "constant_rows",
    "signature_rows",
    "SourceMapEntry",
    "diagnose_runtime_error",
    "LANGUAGE_VERSION",
]

from .diagnostics import diagnose_runtime_error
from .version import LANGUAGE_VERSION
