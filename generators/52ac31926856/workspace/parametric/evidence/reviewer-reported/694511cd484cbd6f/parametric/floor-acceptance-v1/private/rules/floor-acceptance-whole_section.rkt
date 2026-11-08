(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((bp (first (find-color g 1)))
                  (bc (snd bp))
                  (g2 (set-cell g (fst bp) (snd bp) 0))
                  (red-objs (filter (lambda (o) (= (obj-color o) 2)) (objects g 0)))
                  (candidate-data (filter (lambda (x) x)
                                          (map (lambda (o)
                                                 (let* ((bb (obj-bbox o))
                                                        (frame-r0 (first bb))
                                                        (frame-r1 (third bb))
                                                        (left-wall (find (lambda (c)
                                                                           (= (at g
                                                                                  frame-r0
                                                                                  c)
                                                                              2))
                                                                         (reverse (range 0
                                                                                         bc))))
                                                        (right-wall (let ((rw (find (lambda (c)
                                                                                      (= (at g
                                                                                             frame-r0
                                                                                             c)
                                                                                         2))
                                                                                    (range (+ bc
                                                                                              1)
                                                                                           w))))
                                                                      (if rw
                                                                          rw
                                                                          (and
                                                                            (= (at g
                                                                                   frame-r0
                                                                                   bc)
                                                                               2)
                                                                            bc)))))
                                                   (and
                                                     (and
                                                       left-wall
                                                       right-wall
                                                       (< left-wall right-wall))
                                                     (let* ((sec-c0 (+ left-wall 1))
                                                            (sec-c1 (- right-wall 1))
                                                            (floor-solid (for/and ((c (range sec-c0
                                                                                             (+ sec-c1
                                                                                                1))))
                                                                                  (= (at g
                                                                                         frame-r1
                                                                                         c)
                                                                                     2))))
                                                       (list frame-r0
                                                             frame-r1
                                                             sec-c0
                                                             sec-c1
                                                             floor-solid)))))
                                               red-objs)))
                  (chosen (find (lambda (x) (fifth x)) (sort-by candidate-data first))))
             (if chosen
                 (reduce (lambda (g3 r)
                           (reduce (lambda (g4 c)
                                     (if (zero? (at g4 r c)) (set-cell g4 r c 1) g4))
                                   g3
                                   (range (third chosen) (+ (fourth chosen) 1))))
                         g2
                         (range (first chosen) (second chosen)))
                 (reduce (lambda (g3 c) (set-cell g3 (- h 1) c 1)) g2 (range 0 w)))))))