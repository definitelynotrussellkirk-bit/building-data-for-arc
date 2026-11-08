(rule!
  (let ((dummy 0))
    (define (crop-obj obj)
      (subgrid g (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj)))
    (define (min-nonzero crop)
      (apply min (filter (lambda (v) (not (= v 0))) (apply append crop))))
    (define items
      (sort (map (lambda (obj)
                   (let ((crop (crop-obj obj)))
                     (list (obj-size obj) (rows crop) (cols crop) (min-nonzero crop) crop)))
                 (objects g 0))
            (lambda (a b)
              (cond [(not (= (first a) (first b))) (< (first a) (first b))]
                    [(not (= (second a) (second b))) (< (second a) (second b))]
                    [(not (= (third a) (third b))) (< (third a) (third b))]
                    [else (< (fourth a) (fourth b))]))))
    (define crops (map fifth items))
    (define out-h (apply max (map rows crops)))
    (define out-w (+ (apply + (map cols crops)) (max 0 (- (length crops) 1))))
    (let pack ([remaining crops] [c0 0] [out (empty-grid out-h out-w 0)])
      (if (empty? remaining)
          out
          (let* ((crop (first remaining))
                 (r0 (- out-h (rows crop)))
                 (next (for*/fold ([acc out])
                                   ([r (in-range (rows crop))]
                                    [c (in-range (cols crop))])
                         (let ((v (at crop r c)))
                           (if (= v 0) acc (set-cell acc (+ r0 r) (+ c0 c) v))))))
            (pack (rest remaining) (+ c0 (cols crop) 1) next))))))