(rule!
 ;; Four distinct colored pieces tile a solid square after quarter-turns.
 ;; Gray 5 belongs to the orange 7 piece and anchors the instructed corner.
 ;; Group by color: a piece may contain cells connected only diagonally.
 ;; First place the marker piece; its occupied cells constrain completion.
 ;; Preserve colors and use rotations only, never reflections. The declared
 ;; input grammar has exactly one reconstruction at the instructed corner.
 (lambda (g)
   (let ()
     (define anchor-corner 'northwest)
     (define cells
       (for*/list ((r (range 0 (length g)))
                   (c (range 0 (length (first g))))
                   #:when (positive? (list-ref (list-ref g r) c)))
         (list r c (list-ref (list-ref g r) c))))
     (define side
       (let seek ((n 1))
         (cond ((= (* n n) (length cells)) n)
               ((> (* n n) (length cells))
                (error 'jigsaw "Non-square total piece area"))
               (else (seek (+ n 1))))))
     (define target-column (if (eq? anchor-corner 'northwest) 0 (- side 1)))
     (define (cell-less? a b)
       (or (< (first a) (first b))
           (and (= (first a) (first b)) (< (second a) (second b)))))
     (define (normalize piece)
       (define top (apply min (map first piece)))
       (define left (apply min (map second piece)))
       (sort (map (lambda (p)
                    (list (- (first p) top) (- (second p) left) (third p)))
                  piece) cell-less?))
     (define (turn piece)
       (normalize (map (lambda (p) (list (second p) (- (first p)) (third p))) piece)))
     (define (orientations piece)
       (define a (normalize piece))
       (define b (turn a))
       (define c (turn b))
       (remove-duplicates (list a b c (turn c))))
     (define (translate piece dr dc)
       (map (lambda (p) (list (+ dr (first p)) (+ dc (second p)) (third p))) piece))
     (define (inside? piece)
       (andmap (lambda (p)
                  (and (<= 0 (first p)) (< (first p) side)
                       (<= 0 (second p)) (< (second p) side))) piece))
     (define (position p) (+ (* side (first p)) (second p)))
     (define (mask piece)
       (for/fold ((bits 0)) ((p piece))
         (bitwise-ior bits (arithmetic-shift 1 (position p)))))
     (define anchor
       (filter (lambda (p) (or (= (third p) 5) (= (third p) 7))) cells))
     (define colors
       (sort (remove-duplicates
              (map third (filter (lambda (p) (and (!= (third p) 5) (!= (third p) 7))) cells))) <))
     (define anchors
       (filter inside?
         (map (lambda (piece)
                (define marker (first (filter (lambda (p) (= (third p) 5)) piece)))
                (translate piece (- (first marker)) (- target-column (second marker))))
              (orientations anchor))))
     (define placements
       (for*/list ((id (range 0 (length colors)))
                   (piece (orientations (filter (lambda (p) (= (third p) (list-ref colors id))) cells)))
                   (dr (range 0 (- side (apply max (map first piece)))))
                   (dc (range 0 (- side (apply max (map second piece))))))
         (define moved (translate piece dr dc))
         (list (arithmetic-shift 1 id) (mask moved) moved)))
     (define by-cell
       (let ((table (make-vector (* side side) (list))))
         (for-each
           (lambda (placement)
             (for-each (lambda (p)
                         (define i (position p))
                         (vector-set! table i (cons placement (vector-ref table i))))
                       (third placement)))
           placements)
         table))
     (define full-mask (- (arithmetic-shift 1 (* side side)) 1))
     (define (first-empty occupied)
       (let scan ((i 0))
         (if (zero? (bitwise-and occupied (arithmetic-shift 1 i))) i (scan (+ i 1)))))
     (define (complete occupied used chosen)
       (if (= occupied full-mask)
           chosen
           (let try ((choices (vector-ref by-cell (first-empty occupied))))
             (cond
               ((null? choices) #f)
               (else
                 (define placement (first choices))
                 (define answer
                   (and (zero? (bitwise-and used (first placement)))
                        (zero? (bitwise-and occupied (second placement)))
                        (complete (bitwise-ior occupied (second placement))
                                  (bitwise-ior used (first placement))
                                  (cons (third placement) chosen))))
                 (if answer answer (try (rest choices))))))))
     (define solution
       (let try-anchor ((choices anchors))
         (cond
           ((null? choices) (error 'jigsaw "No rotation-only reconstruction"))
           (else
             (define piece (first choices))
             (define answer (complete (mask piece) 0 (list piece)))
             (if answer answer (try-anchor (rest choices)))))))
     (define output (make-vector (* side side) 0))
     (for-each (lambda (piece)
                 (for-each (lambda (p) (vector-set! output (position p) (third p))) piece))
               solution)
     (for/list ((r (range 0 side)))
       (for/list ((c (range 0 side)))
         (vector-ref output (+ (* side r) c)))))))
