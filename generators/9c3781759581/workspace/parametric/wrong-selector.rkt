(rule!
 (let* ((selector-count (length (find-color g 2)))
        (target-color (if (= (modulo selector-count 2) 1) 9 5))
        (bb (bbox-of-cells (find-color g target-color))))
   (subgrid g (first bb) (second bb) (third bb) (fourth bb))))
