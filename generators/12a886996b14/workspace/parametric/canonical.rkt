(rule!
  (let* ((bb2 (bbox-of-cells (find-color g 2)))
         (bb3 (bbox-of-cells (find-color g 3)))
         (dr (- (first bb3) (first bb2)))
         (dc (- (second bb3) (second bb2))))
    (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([p (in-list (find-color g 4))])
      (set-cell out (+ (first p) dr) (+ (second p) dc) 4))))