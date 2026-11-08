(rule!
  (let* ((shape (first (filter (lambda (o) (= (obj-color o) 8)) (objects g 0))))
         (pivot (first (find-color g 9)))
         (code (third (first (filter (lambda (cell)
                                       (let ((v (third cell)))
                                         (and (>= v 1) (<= v 4))))
                                     (grid-cells g)))))
         (targets
          (map (lambda (p)
                 (let* ((dr (- (first p) (first pivot)))
                        (dc (- (second p) (second pivot))))
                   (cond [(= code 1)
                          (list (+ (first pivot) dr) (+ (second pivot) dc))]
                         [(= code 2)
                          (list (+ (first pivot) dc) (- (second pivot) dr))]
                         [(= code 3)
                          (list (- (first pivot) dr) (- (second pivot) dc))]
                         [else
                          (list (- (first pivot) dc) (+ (second pivot) dr))])))
               (obj-cells shape)))
         (cue-cells
          (filter (lambda (cell)
                    (let ((v (third cell))
                          (r (first cell))
                          (c (second cell)))
                      (and (>= v 5)
                           (<= v 7)
                           (ormap (lambda (p)
                                    (= (+ (abs (- r (first p)))
                                          (abs (- c (second p))))
                                       1))
                                  targets))))
                  (grid-cells g)))
         (relay-color (third (first cue-cells)))
         (stamped
          (foldl (lambda (p out)
                   (let ((r (first p)) (c (second p)))
                     (if (in-bounds? r c (rows g) (cols g))
                         (set-cell out r c 2)
                         out)))
                 g
                 targets)))
    (cellmap stamped
             (r c v)
             (if (= (at g r c) relay-color) 2 v))))
