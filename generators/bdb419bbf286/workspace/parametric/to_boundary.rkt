(rule!
  (let* ((shape (obj-cells (first (filter (lambda (o) (= (obj-color o) 2)) (objects g 0)))))
         (a (first (find-color g 3)))
         (b (first (find-color g 4)))
         (dr (- (first b) (first a)))
         (dc (- (second b) (second a))))
    (for/fold ([out (empty-grid (rows g) (cols g) 0)])
              ([k (in-range 0 (+ (rows g) (cols g)))])
      (paint-cells out
                   (map (lambda (p)
                          (list (+ (first p) (* k dr))
                                (+ (second p) (* k dc))))
                        shape)
                   8))))
