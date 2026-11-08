(rule!
  (let* ((src (first (find-color g 2)))
         (dst (first (find-color g 1)))
         (dr (- (first dst) (first src)))
         (dc (- (second dst) (second src)))
         (moved (map (lambda (p) (list (+ (first p) dr) (+ (second p) dc)))
                     (find-color g 3))))
    (recolor-cells (empty-grid h w 0) moved 3)))
