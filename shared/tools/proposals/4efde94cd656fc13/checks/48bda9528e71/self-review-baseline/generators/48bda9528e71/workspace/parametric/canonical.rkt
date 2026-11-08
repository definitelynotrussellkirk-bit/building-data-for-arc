(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hh (rows g))
                  (ww (cols g))
                  (bg 8)
                  (cells (for*/list ((r (range 0 hh)) (c (range 0 ww)) #:when (!= (at g r c) bg))
                           (list r c (at g r c))))
                  (freq (make-hash))
                  (dummy (for ((cell cells))
                           (hash-set! freq
                                      (third cell)
                                      (+ 1 (hash-ref freq (third cell) 0)))))
                  (inner-color (car (sort (hash-keys freq)
                                          (lambda (a b)
                                            (< (hash-ref freq a 0) (hash-ref freq b 0))))))
                  (result (make-hash)))
             (for* ((r (range 0 hh)) (c (range 0 ww))) (hash-set! result (list r c) bg))
             (for ((r (range 0 hh)))
               (let ((row-cs (map second
                                  (filter (lambda (cell) (= (first cell) r)) cells))))
                 (unless
                   (null? row-cs)
                   (let ((left (min-list row-cs))
                         (right (max-list row-cs)))
                     (when
                       (>= (- left 1) 0)
                       (hash-set! result (list r (- left 1)) inner-color))
                     (when
                       (< (+ right 1) ww)
                       (hash-set! result (list r (+ right 1)) inner-color))))))
             (for ((c (range 0 ww)))
               (let ((col-rs (map first
                                  (filter (lambda (cell) (= (second cell) c)) cells))))
                 (unless
                   (null? col-rs)
                   (let ((top (min-list col-rs))
                         (bot (max-list col-rs)))
                     (when
                       (>= (- top 1) 0)
                       (hash-set! result (list (- top 1) c) inner-color))
                     (when
                       (< (+ bot 1) hh)
                       (hash-set! result (list (+ bot 1) c) inner-color))))))
             (build-grid hh ww (r c) (hash-ref result (list r c) 0))))))