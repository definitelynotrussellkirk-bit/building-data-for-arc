(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define tile-rows (quotient (+ h 1) 4))
             (define tile-cols (quotient (+ w 1) 4))
             (define tile-pos
               (for*/list ((tr (range 0 tile-rows)) (tc (range 0 tile-cols)))
                 (list tr tc)))
             (define (tile-mask tr tc)
               (for*/list ((dr (range 0 3)) (dc (range 0 3)))
                 (if (zero? (at g (+ 1 (* 4 tr) dr) (+ 1 (* 4 tc) dc))) 0 1)))
             (define (tile-has-color? tr tc color)
               (for*/or ((dr (range 0 3)) (dc (range 0 3)))
                        (= (at g (+ 1 (* 4 tr) dr) (+ 1 (* 4 tc) dc)) color)))
             (define seed
               (find-first (lambda (p) (tile-has-color? (first p) (second p) 8))
                           tile-pos))
             (define key-mask (tile-mask (first seed) (second seed)))
             (define key-tiles
               (filter (lambda (p) (equal? (tile-mask (first p) (second p)) key-mask))
                       tile-pos))
             (define (key-tile? tr tc)
               (for/or ((p key-tiles)) (and (= (first p) tr) (= (second p) tc))))
             (define (between? x a b) (or (and (< a x) (< x b)) (and (< b x) (< x a))))
             (define (bridge-tile? tr tc)
               (for/or ((other key-tiles))
                       (or
                         (and
                           (= (first seed) tr)
                           (= (first other) tr)
                           (between? tc (second seed) (second other)))
                         (and
                           (= (second seed) tc)
                           (= (second other) tc)
                           (between? tr (first seed) (first other))))))
             (cellmap g
                      (r c v)
                      (let ((v v))
                        (if (or (zero? v) (zero? (modulo r 4)) (zero? (modulo c 4)))
                            v
                            (let ((tr (quotient r 4))
                                  (tc (quotient c 4)))
                              (cond
                                ((key-tile? tr tc) 8)
                                ((bridge-tile? tr tc) 7)
                                (else v))))))))))