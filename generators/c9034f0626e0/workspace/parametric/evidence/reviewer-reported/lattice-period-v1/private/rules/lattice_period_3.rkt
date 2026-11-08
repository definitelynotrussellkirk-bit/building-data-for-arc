(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hh (rows g))
                  (ww (cols g))
                  (marker #f)
                  (mr 0)
                  (mc 0)
                  (dummy (for* ((r (range 0 hh)) (c (range 0 ww)))
                               (when
                                 (and (not marker) (!= (at g r c) 0) (!= (at g r c) 5))
                                 (set! marker (at g r c))
                                 (set! mr r)
                                 (set! mc c))))
                  (rp (remainder mr 3))
                  (cp (remainder mc 3)))
             (build-grid hh
                         ww
                         (r c)
                         (if (and
                               (= (remainder r 3) rp)
                               (= (remainder c 3) cp)
                               (zero? (at g r c)))
                             marker
                             (at g r c)))))))
