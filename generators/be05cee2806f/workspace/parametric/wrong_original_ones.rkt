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
             (define stage
               (for/fold ((out g))
                 ((obj zero-objs))
                 (if (touches-one? obj) (recolor-cells out (obj-cells obj) 1) out)))
             (grid-from-fn h w
               (lambda (r c)
                 (let ((original (at g r c))
                       (staged (at stage r c)))
                   (if (and (not (= original 0))
                            (not (= original 1))
                            (for/or ((d dirs))
                                    (= (safe-at g
                                                (+ r (first d))
                                                (+ c (second d))
                                                -1)
                                       1)))
                       1
                       staged))))))))
