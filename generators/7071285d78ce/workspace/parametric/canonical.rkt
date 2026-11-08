(rule!
  (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([obj (in-list (objects g 0))])
    (let ((cells (map (lambda (p)
                        (list (+ (obj-r1 obj) (- (second p) (obj-c1 obj)))
                              (+ (obj-c1 obj) (- (first p) (obj-r1 obj)))))
                      (obj-cells obj))))
      (paint-cells out cells (obj-color obj)))))