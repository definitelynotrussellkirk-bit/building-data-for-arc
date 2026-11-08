(rule!
  (let ((dummy 0))
    (for/fold ((out (empty-grid (rows g) (cols g) 0)))
              ((obj (in-list (objects g 0))))
      (let* ((bb (obj-bbox obj))
             (c0 (second bb))
             (c1 (fourth bb))
             (right-gap (- (- (cols g) 1) c1))
             (dc (if (<= c0 right-gap) (- 0 c0) right-gap)))
        (paint-cells out
                     (map (lambda (p)
                            (list (first p) (+ (second p) dc)))
                          (obj-cells obj))
                     (obj-color obj))))))