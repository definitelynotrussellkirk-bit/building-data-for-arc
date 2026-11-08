(rule!
  (let ((dummy 0))
    (for/fold ((out (empty-grid (rows g) (cols g) 0)))
              ((obj (in-list (objects g 0))))
      (let* ((c1 (fourth (obj-bbox obj)))
             (dc (- (- (cols g) 1) c1)))
        (paint-cells out
                     (map (lambda (p)
                            (list (first p) (+ (second p) dc)))
                          (obj-cells obj))
                     (obj-color obj))))))