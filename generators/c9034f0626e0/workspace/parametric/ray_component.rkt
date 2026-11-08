(rule!
 (lambda (g)
   (let* ((h (rows g))
          (w (cols g))
          (marker #f)
          (mr 0)
          (mc 0)
          (find-marker
           (for* ((r (range 0 h)) (c (range 0 w)))
             (when (and (not marker)
                        (!= (at g r c) 0)
                        (!= (at g r c) 5))
               (set! marker (at g r c))
               (set! mr r)
               (set! mc c))))
          (hit-col #f)
          (find-hit
           (when marker
             (for ((c (range (+ mc 1) w)))
               (when (and (not hit-col) (= (at g mr c) 5))
                 (set! hit-col c)))))
          (selected-cells
           (if hit-col
               (connected-region g mr hit-col (lambda (r c v) (= v 5)) 4)
               '()))
          (period (if (= (remainder (length selected-cells) 2) 0) 2 3))
          (rp (remainder mr period))
          (cp (remainder mc period)))
     (if (not marker)
         g
         (build-grid h
                     w
                     (r c)
                     (if (and (= (remainder r period) rp)
                              (= (remainder c period) cp)
                              (zero? (at g r c)))
                         marker
                         (at g r c)))))))
