# Blind solve work log
Only the public challenge presentation was consulted. No generator, rule, canonical reference, prior solve, or private label was opened.
Infrastructure: the initial preparation was killed under memory pressure (wrapper exit 247). After deduplicating identical immutable extracted files with hardlinks, preparation succeeded; all source paths and bytes were preserved.

Hypothesis: extract the largest monochromatic connected object, retain its color and interior zero cells, and crop tightly. Count pixels in each object, not in each color across the scene. Train 1 rejects global color frequency: color 7 totals nine cells split into objects of five and four, while the selected object has six.
Train 0 contains two six-cell objects; the selected red object is encountered first in row-major order. Train 1 likewise chooses the earlier of the two six-cell objects. Train 2 chooses the seven-cell object over a six-cell object.
I used four-neighbor monochromatic connectivity and first row-major object to break equal-size ties. The visible examples constrain area and tie choice but are finite evidence; other connectivity hypotheses may agree. No failed code revision was manufactured.
