(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (cellmap g
                    (r c v)
                    (if (for/or ((dr (list -1 0 1)))
                                (for/or ((dc (list -1 0 1)))
                                        (let ((nr (+ r dr))
                                              (nc (+ c dc)))
                                          (and
                                            (>= nr 0)
                                            (< nr h)
                                            (>= nc 0)
                                            (< nc w)
                                            (= 5 (at g nr nc))))))
                        1
                        0)))))