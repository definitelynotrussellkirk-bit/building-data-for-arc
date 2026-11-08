(rule! (let ((dummy 0))
  (define (s17-split-panel-row grid count)
    (let ((pw (quotient (- (cols grid) (- count 1)) count)))
      (for/list ((i (in-range count)))
        (let ((left (* i (+ pw 1))))
          (grid-from-fn (rows grid) pw
            (lambda (r c) (at grid r (+ left c))))))))
  ;; Stage A performs the exact local three-panel vote. Stage B counts colors
  ;; in that voted grid and keeps only the unique global output mode.
  (let* ((panels (s17-split-panel-row g 3))
         (p0 (first panels))
         (voted
          (grid-from-fn (rows p0) (cols p0)
            (lambda (r c)
              (let* ((vals (map (lambda (p) (at p r c)) panels))
                     (nz (filter (lambda (v) (not (= v 0))) vals)))
                (if (< (length nz) 2)
                    0
                    (let* ((colors (remove-duplicates nz))
                           (best
                            (first
                             (sort colors
                               (lambda (a b)
                                 (let ((ca (count-where (lambda (v) (= v a)) nz))
                                       (cb (count-where (lambda (v) (= v b)) nz)))
                                   (or (> ca cb) (and (= ca cb) (> a b)))))))))
                      best))))))
         (all-votes (apply append voted))
         (nonzero (filter (lambda (v) (not (= v 0))) all-votes)))
    (if (empty? nonzero)
        voted
        (let* ((colors (remove-duplicates nonzero))
               (keep
                (first
                 (sort colors
                   (lambda (a b)
                     (let ((ca (count-where (lambda (v) (= v a)) nonzero))
                           (cb (count-where (lambda (v) (= v b)) nonzero)))
                       (or (> ca cb) (and (= ca cb) (> a b)))))))))
          (grid-from-fn (rows voted) (cols voted)
            (lambda (r c)
              (let ((value (at voted r c)))
                (if (= value keep) value 0)))))))))
