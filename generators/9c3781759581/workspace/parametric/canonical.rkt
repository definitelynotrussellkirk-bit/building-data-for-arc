(rule!
 ;; Crop to the bbox of the maroon(9) markers.
 (let ((bb (bbox-of-cells (find-color g 9)))) (subgrid g (first bb) (second bb) (third bb) (fourth bb))))