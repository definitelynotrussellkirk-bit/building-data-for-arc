(rule! (lambda (grid)
  (let* ((base ((lambda (grid)
         (let* ((h (rows grid))
                (w (cols grid))
                (objs (objects-multicolor grid 0)))
           (foldl (lambda (obj acc)
                    (with-bbox obj
                               (r1 c1 r2 c2)
                               (let* ((cells (obj-cells obj))
                                      (color-freq (map (lambda (col)
                                                         (list col
                                                               (count-if (lambda (p)
                                                                           (= (at grid
                                                                                  (first p)
                                                                                  (second p))
                                                                              col))
                                                                         cells)))
                                                       (remove-duplicates (map (lambda (p)
                                                                                 (at grid
                                                                                     (first p)
                                                                                     (second p)))
                                                                               cells))))
                                      (sorted-colors (sort-by color-freq
                                                              (lambda (f)
                                                                (- (second f)))))
                                      (main-color (first (first sorted-colors)))
                                      (marker-color (first (second sorted-colors)))
                                      (hh (+ 1 (- r2 r1)))
                                      (ww (+ 1 (- c2 c1)))
                                      (ih (- hh 2))
                                      (iw (- ww 2))
                                      (max-dr (quotient (- ih 1) 2))
                                      (max-dc (quotient (- iw 1) 2)))
                                 (build-grid h
                                             w
                                             (r c)
                                             (if (or
                                                   (< r r1)
                                                   (> r r2)
                                                   (< c c1)
                                                   (> c c2))
                                                 (at acc r c)
                                                 (let ((rr (- r r1))
                                                       (cc (- c c1)))
                                                   (cond
                                                     ((or
                                                        (zero? rr)
                                                        (= rr (- hh 1))
                                                        (zero? cc)
                                                        (= cc (- ww 1))) main-color)
                                                     (else (let* ((ir (- rr 1))
                                                                  (ic (- cc 1))
                                                                  (dr (min ir
                                                                           (- ih 1 ir)))
                                                                  (dc (min ic
                                                                           (- iw 1 ic))))
                                                             (if (or
                                                                   (= dr dc)
                                                                   (and
                                                                     (= dr max-dr)
                                                                     (>= dc dr))
                                                                   (and
                                                                     (= dc max-dc)
                                                                     (>= dr dc)))
                                                                 marker-color
                                                                 0))))))))))
                  grid
                  objs))) grid))
         (objs (objects-multicolor grid 0)))
    (define (color-frequencies obj)
      (let ((cells (obj-cells obj)))
        (map (lambda (col)
               (list col
                     (count-if (lambda (p)
                                 (= (at grid (first p) (second p)) col))
                               cells)))
             (remove-duplicates
               (map (lambda (p) (at grid (first p) (second p))) cells)))))
    (define (marker-color obj)
      (first
        (second
          (sort-by (color-frequencies obj)
                   (lambda (f) (- (second f)))))))
    (define (bbox-cells obj)
      (with-bbox obj (r1 c1 r2 c2)
        (positions-in-rect r1 c1 r2 c2)))
    (define (selection-score obj)
               (let ((marker (marker-color obj)))
                 (count-if (lambda (p)
                             (= (at grid (first p) (second p)) marker))
                           (obj-cells obj))))
    (if (empty? objs)
        base
        (let* ((winner (pick-max objs selection-score))
               (marker (marker-color winner)))
          (for/fold ((out base)) ((p (in-list (bbox-cells winner))))
            (if (= (at base (first p) (second p)) marker)
                (set-cell out (first p) (second p) 9)
                out)))))))