(rule! (lambda (g)
  (let* ((stage
           (cellmap g (r c v)
             (if (!= 5 v)
                 v
                 (let ((l (if (and (> c 0) (= 5 (at g r (- c 1)))) 1 0))
                       (ri (if (and (< c (- (cols g) 1)) (= 5 (at g r (+ c 1)))) 1 0))
                       (u (if (and (> r 0) (= 5 (at g (- r 1) c))) 1 0))
                       (d (if (and (< r (- (rows g) 1)) (= 5 (at g (+ r 1) c))) 1 0)))
                   (if (and (= 1 l) (= 1 ri) (= 1 u) (= 1 d)) 2 5)))))
         (separator-col (second (first (find-color g 9))))
         (intermediate
           (length
             (filter (lambda (p) (< (second p) separator-col))
                     (find-color stage 2))))
         (payloads
           (sort
             (filter (lambda (o)
                       (and (= (obj-color o) 3)
                            (> (obj-c1 o) separator-col)))
                     (objects stage 0))
             (lambda (a b)
               (or (< (obj-r1 a) (obj-r1 b))
                   (and (= (obj-r1 a) (obj-r1 b))
                        (< (obj-c1 a) (obj-c1 b)))))))
         (target (list-ref payloads (- intermediate 1))))
    (recolor-cells stage (obj-cells target) 8))))
