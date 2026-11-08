(rule!
  (let ((dummy 0))
    (define (cell<? a b)
      (or (< (first a) (first b))
          (and (= (first a) (first b)) (< (second a) (second b)))))
    (define (norm cells) (sort (normalize-cells cells) cell<?))
    (define (rot cells) (norm (rotate-cells-cw cells)))
    (for/fold ([out g]) ([obj (objects g 0)])
      (let loop ((k 0) (shape (norm (obj-cells obj))) (acc out))
        (if (= k 4)
            acc
            (loop (+ k 1)
                  (rot shape)
                  (paint-cells acc
                               (map (lambda (p) (list (+ (obj-r1 obj) (first p)) (+ (obj-c1 obj) (second p)))) shape)
                               (obj-color obj))))))))