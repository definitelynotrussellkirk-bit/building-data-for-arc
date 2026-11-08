# 26872d42d87a

Generator version `3.0.0`; canonical rule hash `bc262329ef0d`.

The selected rule copies the input and changes an original background cell from `0` to `6` exactly when its immediate **horizontal** neighbours are both `6`. Existing cells, wider horizontal gaps, vertical `6,0,6` patterns, and color-5 decorations remain unchanged.

Ordinary inputs use one of the five exact canonical size profiles: `8×10`, `9×11`, `10×12`, `9×10`, or `10×11`. Every input has three rows with true one-cell horizontal gaps, one wider same-row `6...6` near-miss, one vertical `6,0,6` near-miss, and one or two border color-5 decorations. Thus each individual example distinguishes the authority from both “fill the whole row span” and “apply the local rule vertically too.”

The only advertised exact control is `scene_profile`; default sampling cycles through all five profiles in every difficulty band. The focused qualification tool is `workspace/qualify.py`, and its usage and limits are documented in `workspace/README.md`.
