(rule!
 ;; Two endpoint dots (the color appearing exactly twice) and a stack
 ;; of stripe walls, each pierced by waypoint marks. Route the path:
 ;; drop from the upper endpoint, elbow one row above each stripe over
 ;; to its waypoint column (middle mark when several), punch through,
 ;; and finally hook over to the lower endpoint. Vertical stripes are
 ;; solved by transposing in and out.
 (lambda (g)
   (let ()
     (define freq (color-frequency g))
     (define bg (mode g))
     (define ep-color
       (find-first (lambda (c) (= (hash-ref freq c 0) 2))
                   (grid-colors g)))
     (define others
       (filter (lambda (c) (and (not (= c bg)) (not (= c ep-color))))
               (grid-colors g)))
     (define stripe-color
       (find-first (lambda (c) (> (hash-ref freq c 0) 30)) others))
     (define wp-color
       (find-first (lambda (c) (and (not (= c stripe-color))
                                    (< (hash-ref freq c 0) 30)
                                    (> (hash-ref freq c 0) 2)))
                   others))
     (define horiz
       (let ((cells (find-color g stripe-color)))
         (> (max-of (lambda (r) (count-if (lambda (p) (= (first p) r))
                                          cells))
                    (remove-duplicates (map first cells)))
            (max-of (lambda (c) (count-if (lambda (p) (= (second p) c))
                                          cells))
                    (remove-duplicates (map second cells))))))
     (define (solve gg)
       (let* ((hh (rows gg)) (ww (cols gg))
              (stripe-rows
               (filter (lambda (r)
                         (>= (count-if (lambda (c) (= (at gg r c)
                                                      stripe-color))
                                       (range 0 ww))
                             (- ww 5)))
                       (range 0 hh)))
              (eps (find-color gg ep-color))
              (upper? (< (first (first eps)) (first (second eps))))
              (start (if upper? (first eps) (second eps)))
              (goal (if upper? (second eps) (first eps)))
              (wp-cells (find-color gg wp-color))
              (marker-col
               (lambda (sr)
                 (let ((cols (sort (map second
                                        (filter (lambda (p)
                                                  (= (first p) sr))
                                                wp-cells))
                                   <)))
                   (cond ((null? cols) -1)
                         ((= (length cols) 1) (first cols))
                         (else (nth cols (quotient (length cols) 2)))))))
              (vseg (lambda (out r1 r2 c)  ;; inclusive vertical run
                      (recolor-cells out
                                     (map (lambda (r) (list r c))
                                          (range (min r1 r2)
                                                 (+ (max r1 r2) 1)))
                                     ep-color)))
              (hseg (lambda (out r c1 c2)  ;; inclusive horizontal run
                      (recolor-cells out
                                     (map (lambda (c) (list r c))
                                          (range (min c1 c2)
                                                 (+ (max c1 c2) 1)))
                                     ep-color))))
         (let loop ((cur-r (+ (first start) 1))
                    (cur-c (second start))
                    (stripes (map (lambda (sr) (list sr (marker-col sr)))
                                  stripe-rows))
                    (out gg))
           (if (null? stripes)
               (hseg (recolor-cells out
                                    (map (lambda (r) (list r cur-c))
                                         (range cur-r (first goal)))
                                    ep-color)
                     (first goal) cur-c (second goal))
               (let ((sr (first (first stripes)))
                     (mc (second (first stripes))))
                 (loop (+ sr 1) mc (rest stripes)
                       (set-cell (hseg (vseg out cur-r (- sr 1) cur-c)
                                       (- sr 1) cur-c mc)
                                 sr mc ep-color)))))))
     (if horiz (solve g) (transpose (solve (transpose g)))))))