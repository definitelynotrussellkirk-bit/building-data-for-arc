(rule!
 ;; Resize an odd family of parallel straight segments to the length of the
 ;; spatially middle segment.  Preserve the endpoint side whose endpoints form
 ;; the common perpendicular alignment; leave non-segment clutter unchanged.
 (lambda (g)
  (let ()
   (define directions (list (list 'H 0 1) (list 'V 1 0) (list 'D1 1 1) (list 'D2 1 -1)))
   (define (projection p d) (+ (* (first p) (second d)) (* (second p) (third d))))
   (define (offset p d) (+ (* (- (third d)) (first p)) (* (second d) (second p))))
   (define (all-equal? xs) (or (empty? xs) (andmap (lambda (x) (= x (first xs))) (rest xs))))
   (define (line-info obj)
    (let* ([cells (obj-cells obj)] [n (length cells)] [bb (obj-bbox obj)]
           [r1 (first bb)] [c1 (second bb)] [r2 (third bb)] [c2 (fourth bb)]
           [same-r (= r1 r2)] [same-c (= c1 c2)]
           [same-d1 (andmap (lambda (p) (= (- (first p) (second p)) (- (first (first cells)) (second (first cells))))) (rest cells))]
           [same-d2 (andmap (lambda (p) (= (+ (first p) (second p)) (+ (first (first cells)) (second (first cells))))) (rest cells))]
           [d (cond [(and (>= n 2) same-r (= (+ (- c2 c1) 1) n)) (first directions)]
                    [(and (>= n 2) same-c (= (+ (- r2 r1) 1) n)) (second directions)]
                    [(and (>= n 2) same-d1 (= (+ (- r2 r1) 1) n)) (third directions)]
                    [(and (>= n 2) same-d2 (= (+ (- r2 r1) 1) n)) (fourth directions)]
                    [else #f])])
     (if d
         (let* ([ordered (sort cells (lambda (a b) (< (projection a d) (projection b d))))]
                [start (first ordered)] [end (last ordered)])
          (hash 'color (obj-color obj) 'cells cells 'length n 'direction (first d)
                'd d 'start start 'end end))
         #f)))
   (define candidates (filter (lambda (x) x) (map line-info (objects-8 g 7))))
   (define (for-dir d) (filter (lambda (x) (eq? (hash-ref x 'direction) (first d))) candidates))
   (define best-d
    (for/fold ([best (first directions)]) ([d (in-list (rest directions))])
     (let* ([here (for-dir d)] [prior (for-dir best)]
            [hc (length here)] [pc (length prior)]
            [hs (apply + (cons 0 (map (lambda (x) (hash-ref x 'length)) here)))]
            [ps (apply + (cons 0 (map (lambda (x) (hash-ref x 'length)) prior)))])
      (if (or (> hc pc) (and (= hc pc) (> hs ps))) d best))))
   (define raw-lines (for-dir best-d))
   (define starts-aligned? (all-equal? (map (lambda (x) (projection (hash-ref x 'start) best-d)) raw-lines)))
   (define ends-aligned? (all-equal? (map (lambda (x) (projection (hash-ref x 'end) best-d)) raw-lines)))
   (define anchor-side (if starts-aligned? 'start 'end))
   (define lines
    (sort
     (map (lambda (x)
            (let ([anchor (hash-ref x anchor-side)])
             (hash-set (hash-set x 'anchor anchor) 'offset (offset anchor best-d))))
          raw-lines)
     (lambda (a b)
      (let ([ao (hash-ref a 'offset)] [bo (hash-ref b 'offset)])
       (if (= ao bo) (cell< (hash-ref a 'anchor) (hash-ref b 'anchor)) (< ao bo))))))
   (define target (hash-ref (list-ref lines (quotient (length lines) 2)) 'length))
   (define dr (second best-d))
   (define dc (third best-d))
   (define sign (if (eq? anchor-side 'start) 1 -1))
   (define erased
    (for/fold ([out g]) ([line lines])
     (for/fold ([acc out]) ([p (hash-ref line 'cells)])
      (set-cell acc (first p) (second p) 7))))
   (define normalized-cells
    (map (lambda (line)
          (let ([a (hash-ref line 'anchor)])
           (for/list ([k (in-range target)])
            (list (+ (first a) (* sign k dr)) (+ (second a) (* sign k dc))))))
         lines))
   (define normalized
    (for/fold ([out erased]) ([line lines] [cells normalized-cells])
     (for/fold ([acc out]) ([p cells])
      (set-cell acc (first p) (second p) (hash-ref line 'color)))))
   (define neighbor-deltas '((-1 -1) (-1 0) (-1 1) (0 -1) (0 1) (1 -1) (1 0) (1 1)))
   (define (contact-color source cells-by-line)
    (define contacts
     (remove-duplicates
      (for/list ([line lines] [cells cells-by-line]
                 #:when
                 (for/or ([p cells])
                  (for/or ([d neighbor-deltas])
                   (let ([r (+ (first p) (first d))] [c (+ (second p) (second d))])
                    (and (in-bounds? r c (rows source) (cols source)) (= (at source r c) 4))))))
       (hash-ref line 'color))))
    (if (= (length contacts) 1) (first contacts) #f))
   (define (recolor-receivers source color)
    (if color (map-grid source (lambda (r c v) (if (= v 4) color v))) source))
   (recolor-receivers normalized (contact-color normalized normalized-cells)))))
