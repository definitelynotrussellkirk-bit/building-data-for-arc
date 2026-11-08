(rule!
  (let ((dummy 0))
    (define h (rows g))
    (define w (cols g))
    (define (side-count obj)
      (+ (if (= (obj-r1 obj) 0) 1 0)
         (if (= (obj-r2 obj) (- h 1)) 1 0)
         (if (= (obj-c1 obj) 0) 1 0)
         (if (= (obj-c2 obj) (- w 1)) 1 0)))
    (define stage-a
      (for/fold ([out g]) ([obj (filter (lambda (o) (and (= (obj-color o) 7) (= (side-count o) 1))) (objects g 0))])
        (paint-cells out (obj-cells obj) 5)))
    (define remaining
      (filter (lambda (o) (= (obj-color o) 7)) (objects stage-a 0)))
    (define selected
      (foldl (lambda (obj best)
               (if (< (obj-size obj) (obj-size best)) obj best))
             (first remaining)
             remaining))
    (paint-cells stage-a (obj-cells selected) 1)))