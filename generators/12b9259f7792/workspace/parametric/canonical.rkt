(rule!
  (let ((dummy 0))
    (define markers (filter (lambda (cell) (and (>= (third cell) 1) (<= (third cell) 4))) (grid-cells g)))
    (define (dist m obj)
      (apply min
             (map (lambda (p)
                    (+ (abs (- (first p) (first m))) (abs (- (second p) (second m)))))
                  (obj-cells obj))))
    (for/fold ([out g]) ([obj (in-list (filter (lambda (o) (= (obj-color o) 5)) (objects g 0)))])
      (let ((best (first (sort markers (lambda (a b) (< (dist a obj) (dist b obj)))))))
        (paint-cells out (obj-cells obj) (third best))))))