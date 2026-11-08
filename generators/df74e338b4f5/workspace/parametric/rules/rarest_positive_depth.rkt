(rule!
  (let ((dummy 0))
    (define (rect-frame? obj)
      (and (= (obj-color obj) 9)
           (>= (obj-h obj) 3)
           (>= (obj-w obj) 3)
           (= (obj-size obj) (- (* (obj-h obj) (obj-w obj))
                                (* (- (obj-h obj) 2) (- (obj-w obj) 2))))
           (all? (lambda (p)
                   (or (= (first p) (obj-r1 obj))
                       (= (first p) (obj-r2 obj))
                       (= (second p) (obj-c1 obj))
                       (= (second p) (obj-c2 obj))))
                 (obj-cells obj))))
    (define frames (filter rect-frame? (objects g 0)))
    (define (marker? p)
      (let ((v (at g (first p) (second p))))
        (and (not (= v 0)) (not (= v 9)))))
    (define markers (filter marker? (grid-positions g)))
    (define (depth-at r c)
      (count-where
        (lambda (obj)
          (and (> r (obj-r1 obj)) (< r (obj-r2 obj))
               (> c (obj-c1 obj)) (< c (obj-c2 obj))))
        frames))
    (define positive-markers
      (filter (lambda (p) (> (depth-at (first p) (second p)) 0)) markers))
    (define selected-marker
      (if (empty? positive-markers)
          #f
          (pick-min
            positive-markers
            (lambda (p)
              (let ((d (depth-at (first p) (second p))))
                (+ (* 100
                      (count-where
                        (lambda (q)
                          (= (depth-at (first q) (second q)) d))
                        positive-markers))
                   (- (length frames) d)))))))
    (define selected-depth
      (if selected-marker
          (depth-at (first selected-marker) (second selected-marker))
          0))
    (grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (let ((v (at g r c)))
          (if (or (= v 0) (= v 9))
              v
              (let ((d (depth-at r c)))
                (if (= d selected-depth) d v))))))))
