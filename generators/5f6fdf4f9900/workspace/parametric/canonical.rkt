(rule! (lambda (g)
         (let* ((n (length (filter (lambda (v) (!= v 0)) (grid-colors g))))
                (oh (* h n))
                (ow (* w n)))
           (build-grid oh
                       ow
                       (br bc)
                       (let* ((r (quotient br n))
                              (c (quotient bc n))
                              (lr (modulo br n))
                              (lc (modulo bc n))
                              (v (at g r c)))
                         (if (!= v 0)
                             v
                             (let* ((cands (filter (lambda (x) x)
                                                   (map (lambda (d)
                                                          (let* ((dr2 (first d))
                                                                 (dc2 (second d))
                                                                 (nr (+ r dr2))
                                                                 (nc (+ c dc2)))
                                                            (and
                                                              (in-bounds? nr nc h w)
                                                              (!= (at g nr nc) 0)
                                                              (zero? (at g nr c))
                                                              (zero? (at g r nc))
                                                              (if (= dr2 dc2)
                                                                  (if (= lr lc) 2 0)
                                                                  (if (= lr
                                                                         (- (- n 1) lc))
                                                                      2
                                                                      0)))))
                                                        diagonal-deltas)))
                                    (found (if (null? cands) 0 (first cands))))
                               found)))))))