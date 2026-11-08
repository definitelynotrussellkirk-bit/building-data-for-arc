(rule!
  ;; Red (2) is the source marker and green (3) is the destination marker.
  (let* ((src (first (find-color g 2)))
         (dst (first (find-color g 3)))
         (dr (- (first dst) (first src)))
         (dc (- (second dst) (second src))))
    ;; Copy only payload cells to a blank grid, shifted by the 2->3 vector.
    (foldl (lambda (cell out)
             (let* ((r (first cell)) (c (second cell)) (v (third cell))
                    (nr (+ r dr)) (nc (+ c dc)))
               (if (and (not (= v 0)) (not (= v 2)) (not (= v 3))
                        (in-bounds? nr nc (rows g) (cols g)))
                   (set-cell out nr nc v)
                   out)))
           (empty-grid (rows g) (cols g) 0)
           (grid-cells g))))