# 6d26bc40cbb2

A connected nonzero/non-9 payload and exactly two maroon (9) markers are placed on a 0 background. Reading the markers in row-major order gives a translation vector. Remove both markers, keep the original payload, and overlay a copy shifted by that vector; the shifted copy wins on overlap and is clipped at the grid boundary. Ordinary draws cover both fully visible and clipped copies and periodically match canonical scale.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
