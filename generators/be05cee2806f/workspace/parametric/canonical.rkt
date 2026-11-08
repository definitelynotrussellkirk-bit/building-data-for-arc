(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define zero-objs
               (filter (lambda (obj) (zero? (obj-color obj))) (objects g -1)))
             (define dirs (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))
             (define (touches-one? obj)
               (for/or ((p (obj-cells obj)))
                       (for/or ((d dirs))
                               (= (safe-at g
                                           (+ (first p) (first d))
                                           (+ (second p) (second d))
                                           -1)
                                  1))))
             (for/fold ((out g))
               ((obj zero-objs))
               (if (touches-one? obj) (recolor-cells out (obj-cells obj) 1) out))))))