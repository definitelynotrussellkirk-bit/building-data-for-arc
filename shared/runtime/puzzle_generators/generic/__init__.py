"""Generic, combinatorially-infinite generator families — SCAFFOLD.

Unlike `per_puzzle/<id>/generator.py` (each welded to ONE fixed canonical
Racket rule, so the set of TASK CONCEPTS is frozen at 3891), these generators
compose random PRIMITIVES into NOVEL task concepts and scale grid size / object
count / palette toward the contest distribution (eval ~18x19, ~29 components).
This is the RE-ARC-style "infinite in concepts, matched to the real
distribution" data source the winners trained on, which our corpus lacks.

Each generated sample is (input, output, program) where:
  - input   : a procedurally built grid (dense / contest-scaled by default)
  - output  : input piped through the composed primitive chain (Python, fast)
  - program : the equivalent Racket program string (the model's supervision
              target — "the model only reads Racket"), so these pairs can train
              both the raw-grid episode model AND the Racket-DSL Qwen model.

Entry point: `puzzle_generators.generic.compose.generate_pair`.
Emit a shard to JSONL with `compose.emit_shard`.
"""
from .compose import generate_pair, emit_shard  # noqa: F401
