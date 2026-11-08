(rule!
 ;; For each non-background color, order its original cells by angle around
 ;; their centroid.  Join consecutive cells (closing the polygon) only when
 ;; they share a row, column, or 45-degree diagonal.  Then treat a singleton
 ;; color adjacent to exactly one differently colored original cell as a
 ;; translated shadow marker: copy that target color's completed polygon by
 ;; the marker-to-anchor offset, painting background only.
 (lambda (g)
  (let ()
   (define bg (mode g -1))
   (define edge-mode 'all_8)
   (define colors (filter (lambda (v) (not (= v bg))) (grid-colors g)))
   (define (inside? p)
    (and (<= 0 (first p)) (< (first p) (rows g))
         (<= 0 (second p)) (< (second p) (cols g))))
   (define (ordered cells)
    (if (<= (length cells) 1) cells
     (let ()
      (define n (length cells))
      (define sr (apply + (map first cells)))
      (define sc (apply + (map second cells)))
      (define (vec p) (list (- (* n (first p)) sr) (- (* n (second p)) sc)))
      (define (angle p) (let ((v (vec p))) (atan (first v) (second v))))
      (define (radius2 p) (let ((v (vec p))) (+ (* (first v) (first v)) (* (second v) (second v)))))
      (sort cells
       (lambda (a b)
        (let ((aa (angle a)) (ab (angle b)))
         (if (= aa ab)
             (if (= (radius2 a) (radius2 b))
                 (or (< (first a) (first b))
                     (and (= (first a) (first b)) (< (second a) (second b))))
                 (< (radius2 a) (radius2 b)))
             (< aa ab))))))))
   (define (aligned? a b)
    (define dr (- (first b) (first a)))
    (define dc (- (second b) (second a)))
    (or (= dr 0) (= dc 0)
        (and (equal? edge-mode 'all_8) (= (abs dr) (abs dc)))))
   (define (segment a b)
    (if (not (aligned? a b)) '()
     (let ()
      (define dr (- (first b) (first a)))
      (define dc (- (second b) (second a)))
      (define steps (max (abs dr) (abs dc)))
      (define sr (cond ((< dr 0) -1) ((> dr 0) 1) (else 0)))
      (define sc (cond ((< dc 0) -1) ((> dc 0) 1) (else 0)))
      (for/list ((k (range (+ steps 1))))
       (list (+ (first a) (* k sr)) (+ (second a) (* k sc)))))))
   (define (complete cells)
    (define ring (ordered cells))
    (define n (length ring))
    (define edge-count (cond ((< n 2) 0) ((= n 2) 1) (else n)))
    (remove-duplicates
     (append cells
      (for/fold ((all '())) ((i (range edge-count)))
       (append all (segment (list-ref ring i) (list-ref ring (modulo (+ i 1) n))))))))
   (define completed
    (map (lambda (color) (list color (complete (find-color g color)))) colors))
   (define (cells-for color) (second (assoc color completed)))
   (define (paint-bg out cells color)
    (for/fold ((acc out)) ((p cells))
     (if (= (at acc (first p) (second p)) bg)
         (set-cell acc (first p) (second p) color)
         acc)))
   (define base
    (for/fold ((out g)) ((entry completed))
     (paint-bg out (second entry) (first entry))))
   (for/fold ((out base)) ((color colors))
    (define markers (find-color g color))
    (if (not (= (length markers) 1)) out
     (let ()
      (define marker (first markers))
      (define anchors
       (filter
        (lambda (p)
         (and (inside? p)
              (not (= (at g (first p) (second p)) bg))
              (not (= (at g (first p) (second p)) color))))
        (map (lambda (d) (list (+ (first marker) (first d)) (+ (second marker) (second d)))) all-8-deltas)))
      (if (not (= (length anchors) 1)) out
       (let ()
        (define anchor (first anchors))
        (define target (at g (first anchor) (second anchor)))
        (define dr (- (first marker) (first anchor)))
        (define dc (- (second marker) (second anchor)))
        (define shifted
         (map (lambda (p) (list (+ (first p) dr) (+ (second p) dc))) (cells-for target)))
        (paint-bg out (filter inside? shifted) color)))))))))
