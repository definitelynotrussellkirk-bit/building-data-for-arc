(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hh (rows g))
                  (ww (cols g))
                  (bg (mode g -1))
                  (objs (objects g bg))
                  (result g))
             (for ((obj objs))
               (when
                 (= (obj-color obj) 1)
                 (with-bbox obj
                            (r1 c1 r2 c2)
                            (let* ((top-full (for/and ((c (range c1 (+ c2 1))))
                                                      (= (at g r1 c) 1)))
                                   (bot-full (for/and ((c (range c1 (+ c2 1))))
                                                      (= (at g r2 c) 1)))
                                   (lft-full (for/and ((r (range r1 (+ r2 1))))
                                                      (= (at g r c1) 1)))
                                   (rgt-full (for/and ((r (range r1 (+ r2 1))))
                                                      (= (at g r c2) 1)))
                                   (open-dir (cond
                                               ((not top-full) 'up)
                                               ((not bot-full) 'down)
                                               ((not lft-full) 'left)
                                               ((not rgt-full) 'right)
                                               (else 'none))))
                              (begin
                                (for* ((r (range (+ r1 1) r2)) (c (range (+ c1 1) c2)))
                                      (when
                                        (= (at result r c) bg)
                                        (set! result (set-cell result r c 2))))
                                (cond
                                  ((equal? open-dir 'left) (for ((r (range (+ r1 1) r2)))
                                      (when
                                        (!= (at g r c1) 1)
                                        (for ((c (range 0 (+ c1 1))))
                                          (when
                                            (= (at result r c) bg)
                                            (set! result (set-cell result r c 2)))))))
                                  ((equal? open-dir 'right) (for ((r (range (+ r1 1) r2)))
                                      (when
                                        (!= (at g r c2) 1)
                                        (for ((c (range c2 ww)))
                                          (when
                                            (= (at result r c) bg)
                                            (set! result (set-cell result r c 2)))))))
                                  ((equal? open-dir 'up) (for ((c (range (+ c1 1) c2)))
                                      (when
                                        (!= (at g r1 c) 1)
                                        (for ((r (range 0 (+ r1 1))))
                                          (when
                                            (= (at result r c) bg)
                                            (set! result (set-cell result r c 2)))))))
                                  ((equal? open-dir 'down) (for ((c (range (+ c1 1) c2)))
                                      (when
                                        (!= (at g r2 c) 1)
                                        (for ((r (range r2 hh)))
                                          (when
                                            (= (at result r c) bg)
                                            (set! result (set-cell result r c 2)))))))))))))
             result))))