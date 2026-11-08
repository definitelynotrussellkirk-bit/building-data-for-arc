(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((blues (find-color g 1))
                  (dots (filter (lambda (p)
                                  (let ((v (at g (first p) (second p))))
                                    (and (!= v 0) (!= v 1))))
                                (grid-positions g))))
             (foldl (lambda (dot acc)
                      (let* ((dr (first dot))
                             (dc (second dot))
                             (color (at g dr dc))
                             (h-blue (find (lambda (b) (= (second b) dc)) blues))
                             (v-blue (find (lambda (b) (= (first b) dr)) blues)))
                        (cond
                          (h-blue (let ((R2 (+ (first h-blue) dr)))
                                    (foldl (lambda (b a)
                                             (set-cell a
                                                       (- R2 (first b))
                                                       (second b)
                                                       color))
                                           acc
                                           blues)))
                          (v-blue (let ((C2 (+ (second v-blue) dc)))
                                    (foldl (lambda (b a)
                                             (set-cell a
                                                       (first b)
                                                       (- C2 (second b))
                                                       color))
                                           acc
                                           blues)))
                          (else acc))))
                    g
                    dots)))))