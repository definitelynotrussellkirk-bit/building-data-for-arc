(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((transformed (cellmap g (r c v) (if (zero? v) 1 0)))
                  (holes-objs (objects transformed 0))
                  (holes (map obj-cells holes-objs))
                  (new-hole-set (make-hash))
                  (path-set (make-hash))
                  (_process
                    (for ((hole holes))
                      (unless
                        (null? hole)
                        (let* ((rs (map first hole))
                               (cs (map second hole))
                               (r1 (min-list rs))
                               (r2 (max-list rs))
                               (c1 (min-list cs))
                               (c2 (max-list cs))
                               (touches-top (zero? r1))
                               (touches-bot (= r2 (- h 1)))
                               (touches-left (zero? c1))
                               (touches-right (= c2 (- w 1)))
                               (mirror
                                 (cond
                                   ((or touches-top touches-bot) 'rows)
                                   ((or touches-left touches-right) 'cols)
                                   (else 'none))))
                          (when
                            (eq? mirror 'rows)
                            (for ((cell hole))
                              (let* ((cr (first cell))
                                     (cc (second cell))
                                     (nr (if (eq? mirror 'rows) (- h 1 cr) cr))
                                     (nc (if (eq? mirror 'rows) cc (- w 1 cc))))
                                (hash-set! new-hole-set (list nr nc) #t)))
                            (cond
                              ((eq? mirror 'rows)
                               (for* ((rr (range 0 h)) (cc cs))
                                 (hash-set! path-set (list rr cc) #t)))
                              (else
                               (for* ((rr rs) (cc (range 0 w)))
                                 (hash-set! path-set (list rr cc) #t))))))))))
             (cellmap g
                      (r c v)
                      (cond
                        ((hash-has-key? new-hole-set (list r c)) 0)
                        ((hash-has-key? path-set (list r c)) 7)
                        (else v)))))))