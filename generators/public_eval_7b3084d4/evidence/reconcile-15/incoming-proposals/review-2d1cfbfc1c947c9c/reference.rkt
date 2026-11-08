(rule!
 ;; The nonzero cells are four colored polyomino pieces.  A single color-5
 ;; cell replaces one cell of its adjacent piece and marks the output's
 ;; top-left corner.  Rotate pieces by quarter turns (never reflect them) and
 ;; exact-cover the unique square; preserve piece colors and the marker.
 (lambda (g)
  (let ()
   (define finish-mode 0)
   (define (lex-cell<? a b)
    (or (< (first a) (first b))
        (and (= (first a) (first b)) (< (second a) (second b)))))
   (define (norm-tagged cells)
    (let ((r0 (apply min (map first cells)))
          (c0 (apply min (map second cells))))
     (sort
      (map (lambda (p) (list (- (first p) r0) (- (second p) c0) (third p))) cells)
      lex-cell<?)))
   (define (rotate-tagged-cw cells)
    (norm-tagged
     (map (lambda (p) (list (second p) (- (first p)) (third p))) cells)))
   (define (rotations shape)
    (let loop ((left 4) (current shape) (seen '()) (out '()))
     (if (= left 0) (reverse out)
      (let ((candidate (norm-tagged current)))
       (loop (- left 1) (rotate-tagged-cw current)
             (if (member candidate seen) seen (cons candidate seen))
             (if (member candidate seen) out (cons candidate out)))))))
   (define (shift cells dr dc)
    (map (lambda (p) (list (+ dr (first p)) (+ dc (second p)))) cells))
   (define (overlap? a b) (ormap (lambda (p) (member p b)) a))
   (define marker (first (find-color g 5)))
   (define near-colors
    (remove-duplicates
     (filter (lambda (v) (and (not (= v 0)) (not (= v 5))))
      (for/list ((d cardinal-deltas)
                 #:when (in-bounds? (+ (first marker) (first d))
                                    (+ (second marker) (second d))
                                    (rows g) (cols g)))
       (at g (+ (first marker) (first d)) (+ (second marker) (second d)))))))
   (define marker-color (first near-colors))
   (define colors
    (sort (filter (lambda (v) (and (not (= v 0)) (not (= v 5))))
                  (grid-colors g)) <))
   (define pieces
    (for/list ((color colors))
     (list color
      (norm-tagged
       (append
        (map (lambda (p) (list (first p) (second p) #f)) (find-color g color))
        (if (= color marker-color)
            (list (list (first marker) (second marker) #t))
            '()))))))
   (define total-area (apply + (map (lambda (piece) (length (second piece))) pieces)))
   (define side (for/first ((s (range 1 31)) #:when (= (* s s) total-area)) s))
   (unless side (error '7b3084d4 "piece areas do not form a square"))
   (define all-placements
    (apply append
     (for/list ((piece pieces))
      (let ((color (first piece)))
       (apply append
        (for/list ((oriented (rotations (second piece))))
         (let* ((coords (map (lambda (p) (list (first p) (second p))) oriented))
                (height (+ 1 (apply max (map first coords))))
                (width (+ 1 (apply max (map second coords))))
                (marks (filter third oriented))
                (offsets
                 (if (empty? marks)
                  (for*/list ((dr (range 0 (+ 1 (- side height))))
                              (dc (range 0 (+ 1 (- side width)))))
                   (list dr dc))
                  (let ((m (first marks)))
                   (list (list (- (first m)) (- (second m))))))))
          (for/list ((offset offsets)
                     #:when
                     (all? (lambda (p) (in-bounds? (first p) (second p) side side))
                           (shift coords (first offset) (second offset))))
           (list color (shift coords (first offset) (second offset)))))))))))
   (define full-cells
    (for*/list ((r (range 0 side)) (c (range 0 side))) (list r c)))
   (define (search occupied remaining selected)
    (if (empty? remaining)
     (if (= (length occupied) total-area) (reverse selected) #f)
     (let* ((target (first (filter (lambda (p) (not (member p occupied))) full-cells)))
            (options
             (filter
              (lambda (placement)
               (and (member (first placement) remaining)
                    (member target (second placement))
                    (not (overlap? (second placement) occupied))))
              all-placements)))
      (let try ((choices options))
       (if (empty? choices) #f
        (let* ((placement (first choices))
               (result
                (search (append (second placement) occupied)
                        (remove (first placement) remaining)
                        (cons placement selected))))
         (if result result (try (rest choices)))))))))
   (define packed (search '() colors '()))
   (unless packed (error '7b3084d4 "pieces cannot tile square"))
   (define owner
    (build-grid side side (r c)
     (first
      (first
       (filter (lambda (placement) (member (list r c) (second placement))) packed)))))
   (define largest-color
    (first (pick-max pieces (lambda (piece) (length (second piece))))))
   (define smallest-color
    (first (pick-min pieces (lambda (piece) (length (second piece))))))
   (define (input-distance color)
    (let ((cells
           (append (find-color g color)
                   (if (= color marker-color) (list marker) '()))))
     (apply min
      (map (lambda (p)
            (+ (- (rows g) 1 (first p)) (- (cols g) 1 (second p))))
           cells))))
   (define nearest-input-color (pick-min colors input-distance))
   (define selected-color
    (cond
     ((= finish-mode 1) (at owner (- side 1) (- side 1)))
     ((= finish-mode 2) largest-color)
     ((= finish-mode 3) smallest-color)
     ((= finish-mode 4) (at owner 0 (- side 1)))
     ((= finish-mode 5) (at owner (- side 1) 0))
     ((= finish-mode 6) marker-color)
     ((= finish-mode 7) nearest-input-color)
     (else -1)))
   (build-grid side side (r c)
    (if (and (= r 0) (= c 0)) 5
     (let ((color (at owner r c)))
      (if (= color selected-color) 5 color)))))))
