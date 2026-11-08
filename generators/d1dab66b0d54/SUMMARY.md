# d1dab66b0d54

An equally spaced green guide marks a positive row or column interval. A red 3×3 ring is centred on one guide cell. Erase the ring and translate every red cell forward by one guide interval, leaving the green guide unchanged.

Kind: `per_puzzle`. Selected generator version: `2.1.0` (repaired from imported `2.0.1`).
Approval is derived by the catalog from current code and retained evidence.

A separate proposed adapter in `workspace/parametric/` keeps the exact canonical `forward` program as default and adds a `backward` direction. Its episode builder now uses a bounded deterministic novelty retry, including a regression for an eight-query collision at seed `-2^63`. Task-local tests, protected-Racket evidence, and source inventory are current; owner qualification remains blocked until the repaired production generator is approved. It is not accepted or training-admitted.
