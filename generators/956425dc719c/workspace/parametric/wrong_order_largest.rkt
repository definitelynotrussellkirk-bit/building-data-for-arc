(rule!
  (let ((dummy 0))
    (define h (rows g))
    (define w (cols g))
    (define (side-count obj)
      (+ (if (= (obj-r1 obj) 0) 1 0)
         (if (= (obj-r2 obj) (- h 1)) 1 0)
         (if (= (obj-c1 obj) 0) 1 0)
         (if (= (obj-c2 obj) (- w 1)) 1 0)))
    (define original-orange
      (filter (lambda (o) (= (obj-color o) 7)) (objects g 0)))
    (define selected-before-a
      (foldl (lambda (obj best)
               (if (> (obj-size obj) (obj-size best)) obj best))
             (first original-orange)
             original-orange))
    (define marked-first
      (paint-cells g (obj-cells selected-before-a) 1))
    (for/fold ([out marked-first])
              ([obj (filter (lambda (o) (and (= (obj-color o) 7) (= (side-count o) 1)))
                            (objects marked-first 0))])
      (paint-cells out (obj-cells obj) 5))))