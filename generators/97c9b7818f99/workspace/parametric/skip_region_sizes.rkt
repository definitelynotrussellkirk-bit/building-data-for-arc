(rule!
  (let ((seeds (filter (lambda (cell) (and (not (= (third cell) 0))
                                           (not (= (third cell) 8))))
                       (grid-cells g))))
    (define (dist cell r c)
      (+ (abs (- r (first cell))) (abs (- c (second cell)))))
    (define (nearest r c)
      (let* ((dmin (apply min (map (lambda (cell) (dist cell r c)) seeds))))
        (filter (lambda (cell) (= (dist cell r c) dmin)) seeds)))
    (define selected
      (first (sort seeds (lambda (a b) (< (third a) (third b))))))
    (define interior
      (for*/list ([r (in-range 1 (- (rows g) 1))]
                  [c (in-range 1 (- (cols g) 1))])
        (list r c)))
    (define (owned-by? seed p)
      (let ((owners (nearest (first p) (second p))))
        (and (= (length owners) 1) (equal? (first owners) seed))))
    (define filled
      (for*/fold ([out g])
                 ([r (in-range 1 (- (rows g) 1))]
                  [c (in-range 1 (- (cols g) 1))])
        (if (= (at out r c) 0)
            (let ((owners (nearest r c)))
              (set-cell out r c
                        (if (>= (length owners) 2)
                            5
                            (third (first owners)))))
            out)))
    (for/fold ([out filled]) ([p (in-list interior)])
      (if (owned-by? selected p)
          (set-cell out (first p) (second p) 9)
          out))))
