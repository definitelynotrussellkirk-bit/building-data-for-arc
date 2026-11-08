(rule!
 ;; Two marked lines cross. Each carries a BASE color plus SPECIAL
 ;; marks; the special marks bound the output rectangle. Weave a plaid
 ;; there on even/odd parity: special vertical rows band between the
 ;; nearest/farthest marks, and whichever line owns the intersection
 ;; cell decides which base dominates the fabric.
 (lambda (g)
   (let ()
     (define horiz-row  ;; the fullest row / column = the two lines
       (pick-max (range 0 h)
                 (lambda (r) (count-if (lambda (c) (> (at g r c) 0))
                                       (range 0 w)))))
     (define vert-col
       (pick-max (range 0 w)
                 (lambda (c) (count-if (lambda (r) (> (at g r c) 0))
                                       (range 0 h)))))
     (define (line-colors vals)  ;; (base special)
       (let* ((base (pick-max (remove-duplicates vals)
                              (lambda (v) (count-if (lambda (x) (= x v))
                                                    vals))))
              (other (filter (lambda (v) (not (= v base))) vals)))
         (list base (if (empty? other) base (first other)))))
     (define horiz-vals
       (filter (lambda (v) (> v 0))
               (map (lambda (c) (if (= c vert-col) 0 (at g horiz-row c)))
                    (range 0 w))))
     (define vert-vals
       (filter (lambda (v) (> v 0))
               (map (lambda (r) (if (= r horiz-row) 0 (at g r vert-col)))
                    (range 0 h))))
     (define horiz-base (first (line-colors horiz-vals)))
     (define horiz-spec (second (line-colors horiz-vals)))
     (define vert-base (first (line-colors vert-vals)))
     (define vert-spec (second (line-colors vert-vals)))
     (define vert-spec-rows
       (filter (lambda (r) (and (not (= r horiz-row))
                                (= (at g r vert-col) vert-spec)))
               (range 0 h)))
     (define horiz-spec-cols
       (filter (lambda (c) (and (not (= c vert-col))
                                (= (at g horiz-row c) horiz-spec)))
               (range 0 w)))
     (define horiz-primary (= (at g horiz-row vert-col) horiz-base))
     (define min-row (min-list (cons horiz-row vert-spec-rows)))
     (define max-row (max-list (cons horiz-row vert-spec-rows)))
     (define min-col (min-list horiz-spec-cols))
     (define max-col (max-list horiz-spec-cols))
     (define near-vs
       (pick-min vert-spec-rows (lambda (r) (abs (- r horiz-row)))))
     (define far-vs
       (pick-max vert-spec-rows (lambda (r) (abs (- r horiz-row)))))
     (build-grid h w (r c)
                 (if (or (< r min-row) (> r max-row)
                         (< c min-col) (> c max-col))
                     0
                     (let ((warp-row (zero? (remainder (- r min-row) 2)))
                           (warp-col (zero? (remainder (- c min-col) 2))))
                       (if warp-row
                           (let ((in-band (and (>= r (min near-vs far-vs))
                                               (<= r (max near-vs
                                                          far-vs)))))
                             (if in-band
                                 (if warp-col
                                     vert-spec
                                     (if (and (= r near-vs) horiz-primary)
                                         horiz-base
                                         vert-base))
                                 (if warp-col horiz-spec vert-base)))
                           (if horiz-primary
                               horiz-base
                               (if warp-col horiz-base vert-base)))))))))
