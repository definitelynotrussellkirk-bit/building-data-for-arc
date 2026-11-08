(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((objs (objects g 0))
                  (obj2 (find (lambda (o) (= (obj-color o) 2)) objs))
                  (obj8 (find (lambda (o) (= (obj-color o) 8)) objs)))
             (with-bbox obj2
                        (r1a c1a r2a c2a)
                        (with-bbox obj8
                                   (r1b c1b r2b c2b)
                                   (let* ((dr (if (< r2a r1b)
                                                  (- (- r1b r2a) 1)
                                                  (if (> r1a r2b) (- (+ r2b 1) r1a) 0)))
                                          (dc (if (< c2a c1b)
                                                  (- (- c1b c2a) 1)
                                                  (if (> c1a c2b) (- (+ c2b 1) c1a) 0)))
                                          (blank (cellmap g (r c v) 0))
                                          (with8 (recolor-cells blank
                                                                (obj-cells obj8)
                                                                8))
                                          (with2 (reduce (lambda (g2 cell)
                                                           (set-cell g2
                                                                     (+ (fst cell) dr)
                                                                     (+ (snd cell) dc)
                                                                     2))
                                                         with8
                                                         (obj-cells obj2))))
                                     with2)))))))