(rule!
  (let* ((reflect-cell
           (find-first
             (lambda (p)
               (let ((v (cell-at g (fst p) (snd p))))
                 (or (= v 2) (= v 3))))
             (grid-positions g)))
         (rotate-cell
           (find-first
             (lambda (p)
               (let ((v (cell-at g (fst p) (snd p))))
                 (or (= v 4) (= v 5) (= v 6) (= v 7))))
             (grid-positions g)))
         (anchor (first (find-color g 9)))
         (template (first (filter (lambda (obj) (= (obj-color obj) 1)) (objects g 0))))
         (reflect-code (cell-at g (fst reflect-cell) (snd reflect-cell)))
         (rotate-code (cell-at g (fst rotate-cell) (snd rotate-cell)))
         (base (normalize-cells (obj-cells template)))
         (rot1 (normalize-cells (rotate-cells-cw base)))
         (rot2 (normalize-cells (rotate-cells-cw rot1)))
         (rot3 (normalize-cells (rotate-cells-cw rot2)))
         (rotated
           (cond
             [(= rotate-code 4) base]
             [(= rotate-code 5) rot1]
             [(= rotate-code 6) rot2]
             [else rot3]))
         (shape (if (= reflect-code 3) (normalize-cells (flip-cells-lr rotated)) rotated)))
    (stamp-normalized-cells g shape (fst anchor) (snd anchor) 8)))