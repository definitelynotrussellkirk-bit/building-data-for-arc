(rule!
 ;; The first row names colors to remove from a structure of arches.
 ;; An arch has a horizontal interior beam and two independent endpoint posts.
 ;; A lower roof terminates an upper post, even at a same-color junction.
 ;; Remove every named structural color, preserving the selector row.
 ;; Posts fall onto material below. A beam stays if material blocks it below
 ;; or both of its lateral endpoints touch surviving material at that height.
 ;; Repeatedly update lower pieces first, resolving equal heights by their
 ;; original row-major IDs. Each move immediately changes later support tests.
 (lambda (g)
   (let ()
     (define lateral-support 'both)
     (define selected
       (filter (lambda (color) (not (= color 0))) (first g)))
     (define (run-right row col)
       (let scan ((end col))
         (if (and (< (+ end 1) w) (not (= (at g row (+ end 1)) 0)))
             (scan (+ end 1))
             end)))
     (define roofs
       (filter
        (lambda (roof) (>= (- (third roof) (second roof)) 2))
        (for*/list ((row (range 2 h)) (col (range 0 w))
                    #:when (and (not (= (at g row col) 0))
                                (or (= col 0) (= (at g row (- col 1)) 0))))
          (list row col (run-right row col)))))
     (define (roof-beams roof)
       (define row (first roof))
       (define right (third roof))
       (let scan ((col (+ (second roof) 1)))
         (if (>= col right)
             (list)
             (let* ((color (at g row col))
                    (end (let same-color ((stop col))
                           (if (and (< (+ stop 1) right)
                                    (= (at g row (+ stop 1)) color))
                               (same-color (+ stop 1))
                               stop)))
                    (cells (for/list ((c (range col (+ end 1)))) (list row c))))
               (cons (list 'horizontal color cells) (scan (+ end 1)))))))
     (define (roof-post roof col)
       (define row (first roof))
       (define color (at g row col))
       (define floor-row
         (apply min
                (cons h
                      (for/list ((lower roofs)
                                 #:when (and (> (first lower) row)
                                             (<= (second lower) col)
                                             (<= col (third lower))))
                        (first lower)))))
       (define end
         (let scan ((stop row))
           (if (and (< (+ stop 1) floor-row)
                    (= (at g (+ stop 1) col) color))
               (scan (+ stop 1))
               stop)))
       (list 'vertical color
             (for/list ((r (range row (+ end 1)))) (list r col))))
     (define pieces
       (apply append
              (for/list ((roof roofs))
                (append (roof-beams roof)
                        (list (roof-post roof (second roof))
                              (roof-post roof (third roof)))))))
     (define active
       (filter (lambda (piece) (not (member (second piece) selected))) pieces))
     (define max-passes (* h (max 1 (length active))))
     (define (piece-bottom piece)
       (apply max (map first (third piece))))
     (define (replace-piece collection index replacement)
       (for/list ((i (range 0 (length collection))))
         (if (= i index) replacement (list-ref collection i))))
     (define (occupied? mask row col)
       (and (<= 0 row) (< row h) (<= 0 col) (< col w)
            (not (= (at mask row col) 0))))
     (define initial-mask
       (for/fold ((mask (empty-grid h w 0))) ((piece active))
         (paint-cells mask (third piece) 1)))
     (define (move-one state index)
       (define collection (first state))
       (define mask (second state))
       (define piece (list-ref collection index))
       (define cells (third piece))
       (define without-self (paint-cells mask cells 0))
       (define shifted
         (map (lambda (cell) (list (+ (first cell) 1) (second cell))) cells))
       (define clear-below
         (for/and ((cell shifted))
           (and (< (first cell) h)
                (not (occupied? without-self (first cell) (second cell))))))
       (define held-laterally
         (and (eq? (first piece) 'horizontal)
              (let* ((row (first (first cells)))
                     (left (apply min (map second cells)))
                     (right (apply max (map second cells)))
                     (left-held (occupied? without-self row (- left 1)))
                     (right-held (occupied? without-self row (+ right 1))))
                (if (eq? lateral-support 'either)
                    (or left-held right-held)
                    (and left-held right-held)))))
       (if (and clear-below (not held-laterally))
           (list (replace-piece collection index
                                (list (first piece) (second piece) shifted))
                 (paint-cells without-self shifted 1)
                 #t)
           state))
     (define settled
       (let settle ((collection active) (mask initial-mask) (remaining max-passes))
         (if (= remaining 0)
             collection
             (let* ((order
                     (sort (range 0 (length collection))
                           (lambda (a b)
                             (let ((a-bottom (piece-bottom (list-ref collection a)))
                                   (b-bottom (piece-bottom (list-ref collection b))))
                               (if (= a-bottom b-bottom)
                                   (< a b)
                                   (> a-bottom b-bottom))))))
                    (next
                     (for/fold ((state (list collection mask #f))) ((index order))
                       (move-one state index))))
               (if (third next)
                   (settle (first next) (second next) (- remaining 1))
                   (first next))))))
     (define header
       (for/fold ((out (empty-grid h w 0))) ((col (range 0 w)))
         (set-cell out 0 col (at g 0 col))))
     (for/fold ((out header)) ((piece settled))
       (paint-cells out (third piece) (second piece))))))
