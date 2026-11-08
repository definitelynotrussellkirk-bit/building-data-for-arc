(rule!
 ;; An isolated dense two-line legend sits on a canvas edge. Its outer line
 ;; supplies owner colors; the adjacent inward line supplies fill colors.
 ;; Recover four-connected enclosed zero regions and their uniform border
 ;; owners. Paint only mapped regions. The alternative selects every tied
 ;; largest enclosed region separately for each owner before painting.
 (lambda (g)
  (let ()
    (define fill-scope 'all)
    (define legend-reading 'edge)
    (define h (rows g))
    (define w (cols g))
    (define (inside? r c) (and (<= 0 r) (< r h) (<= 0 c) (< c w)))
    (define candidates
      (apply append
        (for/list ([o (objects-multicolor g 0)])
          (define colors (remove-duplicates
            (map (lambda (p) (at g (first p) (second p))) (obj-cells o))))
          (if (and (> (length colors) 1) (= (obj-size o) (* (obj-h o) (obj-w o))))
              (filter identity
                (list
                  (and (= (obj-h o) 2) (>= (obj-w o) 2) (= (obj-r1 o) 0) (list 'top o))
                  (and (= (obj-h o) 2) (>= (obj-w o) 2) (= (obj-r2 o) (- h 1)) (list 'bottom o))
                  (and (= (obj-w o) 2) (>= (obj-h o) 2) (= (obj-c1 o) 0) (list 'left o))
                  (and (= (obj-w o) 2) (>= (obj-h o) 2) (= (obj-c2 o) (- w 1)) (list 'right o))))
              '()))))
    (unless (= (length candidates) 1)
      (error 'legend "one unambiguous dense edge legend is required"))
    (define side (first (first candidates)))
    (define legend (second (first candidates)))
    (define pairs
      (if (member side '(top bottom))
          (for/list ([c (in-range (obj-c1 legend) (+ 1 (obj-c2 legend)))])
            (define outer (if (equal? side 'top) 0 (- h 1)))
            (define inner (if (equal? side 'top) 1 (- h 2)))
            (list (at g outer c) (at g inner c)))
          (for/list ([r (in-range (obj-r1 legend) (+ 1 (obj-r2 legend)))])
            (define outer (if (equal? side 'left) 0 (- w 1)))
            (define inner (if (equal? side 'left) 1 (- w 2)))
            (list (at g r outer) (at g r inner)))))
    ;; Only edge reading is exposed by the native contract. These two simple
    ;; alternatives are explicit executable rivals used by the private audit.
    (define read-pairs
      (if (or (equal? legend-reading 'reverse)
              (and (equal? legend-reading 'fixed_top_left) (member side '(bottom right))))
          (map reverse pairs) pairs))
    (unless (= (length read-pairs) (length (remove-duplicates (map first read-pairs))))
      (error 'legend "owner keys must be unique"))
    (define mapping (make-hash (map (lambda (p) (cons (first p) (second p))) read-pairs)))
    (define (boundary-colors cells)
      (remove-duplicates
        (apply append
          (for/list ([p cells])
            (for/list ([d '((-1 0) (1 0) (0 -1) (0 1))]
                       #:when (and (inside? (+ (first p) (first d)) (+ (second p) (second d)))
                                   (not (= (at g (+ (first p) (first d)) (+ (second p) (second d))) 0))))
              (at g (+ (first p) (first d)) (+ (second p) (second d))))))))
    (define holes
      (filter identity
        (for/list ([o (objects g -1)] #:when (= (obj-color o) 0))
          (define cells (obj-cells o))
          (define owners (boundary-colors cells))
          (and (> (obj-r1 o) 0) (< (obj-r2 o) (- h 1))
               (> (obj-c1 o) 0) (< (obj-c2 o) (- w 1))
               (= (length owners) 1)
               (list cells (first owners) (length cells))))))
    ;; A: input-dependent maxima are grouped by the contour owner, not by
    ;; object order, total colored area, bounding-box area, or a global rank.
    (define maxima (make-hash))
    (for ([record holes])
      (define owner (second record))
      (define area (third record))
      (hash-update! maxima owner (lambda (old) (max old area)) area))
    ;; B consumes A's owner-specific result and preserves all maximum ties.
    (define (keep-hole? record)
      (or (equal? fill-scope 'all)
          (= (third record) (hash-ref maxima (second record)))))
    (define paint (make-hash))
    (for ([record holes]
          #:when (and (hash-has-key? mapping (second record)) (keep-hole? record)))
      (for ([p (first record)])
        (hash-set! paint p (hash-ref mapping (second record)))))
    (grid-from-fn h w (lambda (r c) (hash-ref paint (list r c) (lambda () (at g r c))))))))
