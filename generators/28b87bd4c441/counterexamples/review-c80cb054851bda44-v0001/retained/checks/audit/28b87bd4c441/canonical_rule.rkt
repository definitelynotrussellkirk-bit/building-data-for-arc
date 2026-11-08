(rule!
  (let* ((obj (first (filter (lambda (o) (= (obj-color o) 5)) (objects g 0))))
         ;; Position of the first red(2) cell
         ;; It marks the destination bbox origin, which need not be occupied.
         (marker (first (find-color g 2)))
         (dr (- (first marker) (obj-r1 obj)))
         (dc (- (second marker) (obj-c1 obj))))
    (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([p (in-list (obj-cells obj))])
      (set-cell out (+ (first p) dr) (+ (second p) dc) 5))))