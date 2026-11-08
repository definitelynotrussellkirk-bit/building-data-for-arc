(rule!
  (let* ((canonical ;; Uniform divider lines split the board into PANELS. A panel carrying
 ;; cyan(8) marks defines a MASK (its cyan cell positions). Same-size
 ;; panels that agree with it outside the mask and hold ONE nonzero
 ;; color under it are matches: the first match's color is the target,
 ;; and every panel in the marked panel's row/col lattice that is
 ;; target-colored under the mask gets the cyan mask stamped in. A mask
 ;; of FULL cyan rows instead stamps, in each same-column panel, the
 ;; single row made entirely of the modal uniform-row color.
 (lambda (g)
   (let ()
     (define (ranges-between dividers total)  ;; gaps between divider lines
       (let loop ((prev -1) (ds dividers) (acc (list)))
         (cond ((null? ds)
                (reverse (if (<= (+ prev 1) (- total 1))
                             (cons (list (+ prev 1) (- total 1)) acc)
                             acc)))
               (else (loop (first ds) (rest ds)
                           (if (<= (+ prev 1) (- (first ds) 1))
                               (cons (list (+ prev 1) (- (first ds) 1))
                                     acc)
                               acc))))))
     (define row-ranges
       (ranges-between (filter (lambda (r) (row-uniform? g r)) (range 0 h))
                       h))
     (define col-ranges
       (ranges-between (filter (lambda (c) (col-uniform? g c)) (range 0 w))
                       w))
     ;; panel = (ri ci r1 c1 pat has8?)
     (define panels
       (map (lambda (idx)
              (let* ((rr (nth row-ranges (first idx)))
                     (cr (nth col-ranges (second idx)))
                     (pat (subgrid g (first rr) (first cr)
                                   (second rr) (second cr))))
                (list (first idx) (second idx) (first rr) (first cr) pat
                      (any? (lambda (p) (= (at pat (first p) (second p)) 8))
                            (grid-positions pat)))))
            (positions-in-rect 0 0 (- (length row-ranges) 1)
                               (- (length col-ranges) 1))))
     (define (p-ri p) (first p))
     (define (p-ci p) (second p))
     (define (p-r1 p) (third p))
     (define (p-c1 p) (fourth p))
     (define (p-pat p) (fifth p))
     (define (p-has8 p) (sixth p))
     (define (p-h p) (rows (p-pat p)))
     (define (p-w p) (cols (p-pat p)))
     (define (stamp-for out marked)
       (if (not (p-has8 marked))
           out
           (let* ((pat (p-pat marked))
                  (mask (filter (lambda (pos)
                                  (= (at pat (first pos) (second pos)) 8))
                                (grid-positions pat)))
                  (same-shape? (lambda (o)
                                 (and (not (p-has8 o))
                                      (= (p-h o) (p-h marked))
                                      (= (p-w o) (p-w marked)))))
                  (agrees-outside?
                   (lambda (o)
                     (all? (lambda (pos)
                             (= (at pat (first pos) (second pos))
                                (at (p-pat o) (first pos) (second pos))))
                           (filter (lambda (pos) (not (member pos mask)))
                                   (grid-positions pat)))))
                  (mask-val
                   (lambda (o)
                     (let ((u (remove-duplicates
                               (map (lambda (pos)
                                      (at (p-pat o) (first pos)
                                          (second pos)))
                                    mask))))
                       (and (= 1 (length u)) (first u)))))
                  (matches (filter (lambda (o)
                                     (and (same-shape? o)
                                          (agrees-outside? o)
                                          (let ((v (mask-val o)))
                                            (and v (> v 0)))))
                                   panels))
                  (primary
                   (lambda (out2)
                     (let* ((target (mask-val (first matches)))
                            (target-rows
                             (remove-duplicates
                              (cons (p-ri marked)
                                    (map p-ri
                                         (filter (lambda (o)
                                                   (and (= (p-ci o)
                                                           (p-ci marked))
                                                        (= (mask-val o)
                                                           target)))
                                                 matches)))))
                            (target-cols
                             (remove-duplicates
                              (cons (p-ci marked)
                                    (map p-ci
                                         (filter (lambda (o)
                                                   (and (= (p-ri o)
                                                           (p-ri marked))
                                                        (= (mask-val o)
                                                           target)))
                                                 matches))))))
                       (for/fold ((g2 out2)) ((o (in-list panels)))
                         (if (and (member? (p-ri o) target-rows)
                                  (member? (p-ci o) target-cols)
                                  (same-shape? o)
                                  (all? (lambda (pos)
                                          (= (at (p-pat o) (first pos)
                                                 (second pos))
                                             target))
                                        mask))
                             (paint-cells g2
                                          (map (lambda (pos)
                                                 (list (+ (p-r1 o)
                                                          (first pos))
                                                       (+ (p-c1 o)
                                                          (second pos))))
                                               mask)
                                          8)
                             g2)))))
                  (secondary
                   (lambda (out2)
                     (if (null? (filter (lambda (dr)
                                          (all? (lambda (v) (= v 8))
                                                (row pat dr)))
                                        (range 0 (p-h marked))))
                         out2
                         (let* ((col-mates
                                 (filter (lambda (o)
                                           (and (not (p-has8 o))
                                                (= (p-ci o) (p-ci marked))
                                                (= (p-w o) (p-w marked))))
                                         panels))
                                (uniform-vals
                                 (flatmap
                                  (lambda (o)
                                    (flatmap
                                     (lambda (dr)
                                       (let ((rv (row (p-pat o) dr)))
                                         (if (= 1 (length
                                                   (remove-duplicates rv)))
                                             (list (first rv))
                                             (list))))
                                     (range 0 (p-h o))))
                                  col-mates))
                                (base (mode-list uniform-vals)))
                           (if (eq? base #f)
                               out2
                               (for/fold ((g2 out2))
                                         ((o (in-list col-mates)))
                                 (let ((hits (filter
                                              (lambda (dr)
                                                (all? (lambda (v)
                                                        (= v base))
                                                      (row (p-pat o) dr)))
                                              (range 0 (p-h o)))))
                                   (if (= 1 (length hits))
                                       (paint-cells
                                        g2
                                        (positions-in-rect
                                         (+ (p-r1 o) (first hits))
                                         (p-c1 o)
                                         (+ (p-r1 o) (first hits))
                                         (+ (p-c1 o) (p-w o) -1))
                                        8)
                                       g2)))))))))
             (if (null? matches) (secondary out) (primary out)))))
     (for/fold ((out g)) ((m (in-list panels)))
       (stamp-for out m)))))
         (stage (canonical g))
         (original-cyan (grid-from-fn (rows g) (cols g)
                          (lambda (r c) (if (= (at g r c) 8) 2 0))))
         (pieces (objects original-cyan 0))
         (largest-size
           (for/fold ((best 0)) ((piece (in-list pieces)))
             (max best (obj-size piece)))))
    (for/fold ((out stage)) ((piece (in-list pieces)))
      (if (= (obj-size piece) largest-size)
          (recolor-cells out (obj-cells piece) 2)
          out))))