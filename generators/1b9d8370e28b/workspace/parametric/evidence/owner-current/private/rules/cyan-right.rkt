(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let ((tl (let loop ((c 0)) (if (!= (at g 0 c) 2) (at g 0 c) (loop (+ c 1))))))
             (let ((h-split (let loop
                                 ((r 1))
                                 (if (>= r h)
                                     #f
                                     (let ((curr (let lp
                                                      ((c 0))
                                                      (if (!= (at g r c) 2)
                                                          (at g r c)
                                                          (lp (+ c 1))))))
                                       (if (!= tl curr) r (loop (+ r 1)))))))
                   (v-split (let loop
                                 ((c 1))
                                 (if (>= c w)
                                     #f
                                     (let ((curr (let lp
                                                      ((r 0))
                                                      (if (!= (at g r c) 2)
                                                          (at g r c)
                                                          (lp (+ r 1))))))
                                       (if (!= tl curr) c (loop (+ c 1))))))))
               (define (bg-of r c)
                 (if h-split
                     (if (< r h-split) tl (if (= tl 8) 1 8))
                     (if (< c v-split) tl (if (= tl 8) 1 8))))
               (define (rc1 r c) (if v-split (if (< c v-split) 0 v-split) 0))
               (define (rc2 r c) (if v-split (if (< c v-split) v-split w) w))
               (define (red-count r reg-c1 reg-c2)
                 (let loop
                      ((c reg-c1) (cnt 0))
                      (if (>= c reg-c2)
                          cnt
                          (loop (+ c 1) (if (= (at g r c) 2) (+ cnt 1) cnt)))))
               (cellmap g
                        (r c v)
                        (let* ((bg (bg-of r c))
                               (c1 (rc1 r c))
                               (c2 (rc2 r c))
                               (cnt (red-count r c1 c2)))
                          (if (zero? cnt)
                              bg
                              (if (= bg 8)
                                  (if (>= c (- c2 cnt)) 2 bg)
                                  (if (< c (+ c1 cnt)) 2 bg))))))))))