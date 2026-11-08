# Transform script gallery family

`gallery_mode=cumulative` is the byte-exact selected canonical program: emit the
initial crop and every cumulative transform state.

`gallery_mode=final_cue_projection` adds a genuine sequential dependency. Step A
executes the complete key script on the multicolor crop and reads the first
row-major nonzero color of the final state. Step B consumes that input-dependent
color, masks the original crop to all occurrences of it, and then replays the
same cumulative script to form the output gallery. Generated scenes use distinct
directional corner colors plus repeated payload cells, so ignoring the script,
using the original top-left color, applying keys independently, or selecting a
fixed color fails the visible demonstrations.

The canonical output width constrains the lawful 30x30 stress input to a compact
5x5 motif; the stress is positional rather than dense and places keys and motif
against opposite canvas boundaries while keeping the output within 30 columns.
