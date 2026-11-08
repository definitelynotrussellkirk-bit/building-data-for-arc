(rule!
  (let ((dummy 0))
    (define objs (objects g 0))
    (define outlined
      (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([obj (in-list objs)])
        (draw-rect-outline out (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj) (obj-color obj))))
    (define markers (filter (lambda (obj) (= (obj-color obj) 9)) objs))
    (define marker (if (= (length markers) 1) (first markers) #f))
    (define mr (if marker (obj-r1 marker) -1))
    (define mc (if marker (obj-c1 marker) -1))
    (define neighbors
      (filter
        (lambda (p)
          (and (<= 0 (first p)) (< (first p) (rows g))
               (<= 0 (second p)) (< (second p) (cols g))))
        (list (list (- mr 1) mc) (list (+ mr 1) mc)
              (list mr (- mc 1)) (list mr (+ mc 1)))))
    (define hits
      (filter
        (lambda (p)
          (let ((v (at outlined (first p) (second p))))
            (and (!= v 0) (!= v 9))))
        neighbors))
    (define relay-color
      (if (= (length hits) 1)
          (at outlined (first (first hits)) (second (first hits)))
          0))
    (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([obj (in-list objs)])
      (if (= (obj-color obj) relay-color)
          (draw-rect-outline out (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj) (obj-color obj))
          out))))
