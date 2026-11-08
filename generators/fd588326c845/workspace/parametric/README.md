# fd588326c845 native parametric prototype

This adapter preserves the exact canonical `clockwise` program as its default.
Its second episode-fixed setting, `anchor_directed`, first identifies the only
key color occurring once. A top-half anchor selects clockwise rotation; a
bottom-half anchor selects counterclockwise rotation. The selected rotation is
then used to transfer key colors into the expanded cyan silhouette.

Inputs are independent of the selected setting. Their occupancy is invariant
under 180-degree rotation, so clockwise and counterclockwise silhouettes are
identical; asymmetric colors keep the outputs different. The first two
training demonstrations deliberately exercise bottom and top anchors, while
all episodes contain exactly four novel query inputs. The final query is a
30x30 stress case.
