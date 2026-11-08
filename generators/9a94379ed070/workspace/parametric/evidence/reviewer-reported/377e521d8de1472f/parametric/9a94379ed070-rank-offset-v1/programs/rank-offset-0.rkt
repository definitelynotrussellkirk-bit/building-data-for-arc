(rule!
 ;; One tile sits somewhere on a separator lattice (green marks are
 ;; noise). Build the tile's FRACTAL: blocks laid out like the tile's
 ;; own nonzero cells, each holding a copy of the tile, colored cyan(8)
 ;; at the cell whose rank inside the tile equals the block's rank
 ;; among the blocks (the self-position) and red(2) everywhere else.
 (lambda (g)
   (let ()
     (define clean (cellmap g (r c v) (if (= v 3) 0 v)))
     (define sep-rows
       (filter (lambda (r) (all? (lambda (c) (zero? (at clean r c)))
                                 (range 0 w)))
               (range 0 h)))
     (define sep-cols
       (filter (lambda (c) (all? (lambda (r) (zero? (at clean r c)))
                                 (range 0 h)))
               (range 0 w)))
     (define first-row
       (find-first (lambda (r) (any? (lambda (c) (> (at clean r c) 0))
                                     (range 0 w)))
                   (range 0 h)))
     (define first-col
       (find-first (lambda (c) (any? (lambda (r) (> (at clean r c) 0))
                                     (range 0 h)))
                   (range 0 w)))
     (define th
       (let ((nxt (find-first (lambda (r) (> r first-row)) sep-rows)))
         (if nxt (- nxt first-row) (- h first-row))))
     (define tw
       (let ((nxt (find-first (lambda (c) (> c first-col)) sep-cols)))
         (if nxt (- nxt first-col) (- w first-col))))
     (define n-brows (quotient (+ h 1) (+ th 1)))
     (define n-bcols (quotient (+ w 1) (+ tw 1)))
     (define tile  ;; the one block with content
       (find-first
        (lambda (sub) (any? (lambda (v) (> v 0)) (apply append sub)))
        (for*/list ((br (range 0 n-brows)) (bc (range 0 n-bcols)))
          (subgrid clean (* br (+ th 1)) (* bc (+ tw 1))
                   (+ (* br (+ th 1)) (- th 1))
                   (+ (* bc (+ tw 1)) (- tw 1))))))
     (define tile-cells  ;; nonzero tile positions, row-major
       (filter (lambda (p) (> (at tile (first p) (second p)) 0))
               (positions-in-rect 0 0 (- th 1) (- tw 1))))
     (define (rank-of rr cc)  ;; row-major rank among the tile cells
       (count-if (lambda (p) (or (< (first p) rr)
                                 (and (= (first p) rr)
                                      (< (second p) cc))))
                 tile-cells))
     (build-grid h w (r c)
                 (let ((br (quotient r (+ th 1)))
                       (bc (quotient c (+ tw 1)))
                       (tr (remainder r (+ th 1)))
                       (tc (remainder c (+ tw 1))))
                   (if (and (< br n-brows) (< bc n-bcols)
                            (< tr th) (< tc tw)
                            (> (at tile br bc) 0)
                            (> (at tile tr tc) 0))
                       (if (= (rank-of br bc) (rank-of tr tc)) 8 2)
                       0))))))