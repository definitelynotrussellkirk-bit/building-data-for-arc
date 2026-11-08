(rule!
  (let ((dummy 0))
    (for/fold ((out (empty-grid (rows g) (cols g) 0)))
              ((obj (in-list (objects g 0))))
      (paint-cells out
                   (map (lambda (p)
                          (list (first p) (+ (second p) 1)))
                        (obj-cells obj))
                   (obj-color obj)))))