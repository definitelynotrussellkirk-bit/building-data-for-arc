(rule!
 ;; A blue(1) wall has gap OPENINGS — 0-pockets under its top edge,
 ;; walled in on both sides. Gray(5) pieces are keys: a piece turns
 ;; red(2) if it BRANCHES (some cell has 3+ gray neighbors) or if its
 ;; top rows (as tall as an opening) match that opening's shape,
 ;; directly or mirrored. All other cells stay as they are.
 (lambda (g)
   (let ()
     (define (blue? r c) (and (in-bounds? r c h w) (= (at g r c) 1)))
     (define wall-rows
       (filter (lambda (r) (any? (lambda (c) (blue? r c)) (range 0 w)))
               (range 0 h)))
     (define rmin (apply min wall-rows))
     (define rmax (apply max wall-rows))
     (define opencells
       (for*/list ((r (in-range rmin (+ rmax 1))) (c (in-range 0 w))
                   #:when (and (= (at g r c) 0)
                               (any? (lambda (r2) (blue? r2 c))
                                     (range rmin r))
                               (any? (lambda (c2) (blue? r c2))
                                     (range 0 c))
                               (any? (lambda (c2) (blue? r c2))
                                     (range (+ c 1) w))))
         (list r c)))
     (define openings
       (map obj-cells
            (objects (paint-cells (empty-grid h w 0) opencells 1) 0)))
     (define op-norm (map normalize-cells openings))
     (define op-flip
       (map (lambda (ns) (normalize-cells (flip-cells-lr ns))) op-norm))
     (define op-heights
       (map (lambda (o) (+ 1 (- (max-of first o) (min-of first o))))
            openings))
     (define pieces
       (map obj-cells
            (filter (lambda (o) (= (obj-color o) 5)) (objects g 0))))
     (define (branched? piece)
       (any? (lambda (rc)
               (>= (count-if (lambda (d)
                               (member (list (+ (first rc) (first d))
                                             (+ (second rc) (second d)))
                                       piece))
                             cardinal-deltas)
                   3))
             piece))
     (define (matches? piece)
       (let ((top-r (min-of first piece)))
         (any? (lambda (idx)
                 (let ((tn (normalize-cells
                            (filter (lambda (rc)
                                      (< (first rc)
                                         (+ top-r (nth op-heights idx))))
                                    piece))))
                   (or (cells-equal? tn (nth op-norm idx))
                       (cells-equal? tn (nth op-flip idx)))))
               (range 0 (length openings)))))
     ;; Stage A: the full areas of all keys whose top rows fit a lock.
     (define matched-areas
       (map length (filter matches? pieces)))
     ;; Stage B: fitting keys always turn red; a branched key turns red only
     ;; when its full area is one of the input-derived matched-key areas.
     (recolor-cells g
                    (flatmap (lambda (piece)
                               (if (or (matches? piece)
                                       (and (branched? piece)
                                            (member (length piece) matched-areas)))
                                   piece
                                   (list)))
                             pieces)
                    2))))