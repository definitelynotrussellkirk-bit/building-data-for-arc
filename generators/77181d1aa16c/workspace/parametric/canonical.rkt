(rule!
 ;; The largest solid non-background rectangle is the PATTERN, drawn in
 ;; a MAJOR and a MINOR color. It mirrors into a 2x2 arrangement:
 ;; flip-lr to the right, flip-ud below, both on the diagonal.
 ;; Indicator dots dropped outside the pattern tell each mirrored block
 ;; what color its major/minor roles become (a role with no indicator
 ;; vanishes). Rebuild all four blocks on a blank field.
 (lambda (g)
   (let ()
     (define rect  ;; largest all-nonzero rectangle, scan order as tiebreak
       (rest (for*/fold ((best (list 0 0 0 0 0)))
                        ((r1 (range 0 h)) (r2 (range r1 h))
                         (c1 (range 0 w)) (c2 (range c1 w)))
               (if (and (> (* (+ 1 (- r2 r1)) (+ 1 (- c2 c1)))
                           (first best))
                        (all? (lambda (p) (> (at g (first p) (second p))
                                             0))
                              (positions-in-rect r1 c1 r2 c2)))
                   (list (* (+ 1 (- r2 r1)) (+ 1 (- c2 c1))) r1 c1 r2 c2)
                   best))))
     (define pr1 (first rect))
     (define pc1 (second rect))
     (define pr2 (third rect))
     (define pc2 (fourth rect))
     (define ph (+ 1 (- pr2 pr1)))
     (define pw (+ 1 (- pc2 pc1)))
     (define pat (subgrid g pr1 pc1 pr2 pc2))
     (define ranked
       (sort-by (map (lambda (c) (list c (length (find-color pat c))))
                     (filter (lambda (c) (> c 0)) (grid-colors pat)))
                (lambda (f) (- (second f)))))
     (define major (first (first ranked)))
     (define minor (first (second ranked)))
     (define (block-key r c)
       (+ (* 2 (if (< r (+ pr1 ph)) 0 1)) (if (< c (+ pc1 pw)) 0 1)))
     (define (pat-at r c)  ;; pattern value, mirrored per block; #f outside
       (let ((lr (if (< r (+ pr1 ph)) (- r pr1) (- r (+ pr1 ph))))
             (lc (if (< c (+ pc1 pw)) (- c pc1) (- c (+ pc1 pw)))))
         (and (>= lr 0) (< lr ph) (>= lc 0) (< lc pw)
              (at pat
                  (if (>= r (+ pr1 ph)) (- ph 1 lr) lr)
                  (if (>= c (+ pc1 pw)) (- pw 1 lc) lc)))))
     (define indicators  ;; (block-key role-value color) per outside dot
       (map (lambda (p)
              (list (block-key (first p) (second p))
                    (pat-at (first p) (second p))
                    (at g (first p) (second p))))
            (filter (lambda (p)
                      (and (> (at g (first p) (second p)) 0)
                           (not (and (>= (first p) pr1)
                                     (<= (first p) pr2)
                                     (>= (second p) pc1)
                                     (<= (second p) pc2)))))
                    (grid-positions g))))
     (define (mapped key role)
       (if (zero? key)
           role
           (let ((hit (find (lambda (i) (and (= (first i) key)
                                             (= (second i) role)))
                            indicators)))
             (if hit (third hit) 0))))
     (build-grid h w (r c)
                 (let ((pv (pat-at r c)))
                   (cond ((not pv) 0)
                         ((= pv major) (mapped (block-key r c) major))
                         ((= pv minor) (mapped (block-key r c) minor))
                         (else 0)))))))