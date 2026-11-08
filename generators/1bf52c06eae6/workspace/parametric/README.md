# 1bf52c06eae6 native parametric family

- `priority_mode=smallest_first` is the byte-exact canonical program.
- `priority_mode=probe_demote` treats the unique color-9 cell as a probe. It
  derives the first canonical shape square covering that probe, demotes the
  derived color to last priority, removes the instruction probe, and re-renders
  the full square mosaic.
- Episodes support 2–6 demonstrations and exactly four queries. Inputs are
  identical across settings for a given seed/count. The fourth query is 30×30.
- `audit.py` checks both settings against eight named finite rivals over six
  seeds and demonstration counts 2, 3, and 6.
