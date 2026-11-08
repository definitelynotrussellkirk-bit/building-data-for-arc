(rule!
 (lambda (g)
   (let* ((stage-a
            (for/fold ((out g))
                      ((obj (in-list
                              (filter (lambda (obj) (= (obj-color obj) 4))
                                      (objects g 0)))))
              (let ((bb (obj-bbox obj)))
                (paint-cells
                 out
                 (list (list (first bb) (second bb))
                       (list (first bb) (fourth bb))
                       (list (third bb) (second bb))
                       (list (third bb) (fourth bb)))
                 1))))
          (selector
            (find-first
             (lambda (p) (= (at g (first p) (second p)) 2))
             (for*/list ((r (in-range (rows g)))
                         (c (in-range (cols g))))
               (list r c))))
          (hit
            (and selector
                 (find-first
                  (lambda (p) (= (at stage-a (first p) (second p)) 1))
                  (for/list ((c (in-range (+ (second selector) 1) (cols g))))
                    (list (first selector) c)))))
          (right-corner
            (and hit
                 (find-first
                  (lambda (p) (= (at stage-a (first p) (second p)) 1))
                  (for/list ((c (in-range (+ (second hit) 1) (cols g))))
                    (list (first hit) c)))))
          (bottom-corner
            (and hit
                 (find-first
                  (lambda (p) (= (at stage-a (first p) (second p)) 1))
                  (for/list ((r (in-range (+ (first hit) 1) (rows g))))
                    (list r (second hit)))))))
     (if (and hit right-corner bottom-corner)
         (let ((r1 (first hit))
               (c1 (second hit))
               (r2 (first bottom-corner))
               (c2 (second right-corner)))
           (cellmap
            stage-a
            (r c v)
            (if (and (not (= v 1))
                     (or (and (or (= r r1) (= r r2))
                              (<= c1 c) (<= c c2))
                         (and (or (= c c1) (= c c2))
                              (<= r1 r) (<= r r2))))
                3
                v)))
         stage-a))))
