(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         ;; Most common color (the background)
         (bg (mode g 0))
         (colors (filter (lambda (c) (and (not (= c bg)) (not (= c 0))))
                         (grid-colors g))))
    (for/fold ((out g)) ((col colors))
      (let* ((cells (find-color g col))
             ;; Top edge of the bbox
             (sr1 (apply min (map first cells)))
             ;; Bottom edge of the bbox
             (sr2 (apply max (map first cells)))
             ;; Left edge of the bbox
             (sc1 (apply min (map second cells)))
             ;; Right edge of the bbox
             (sc2 (apply max (map second cells)))
             ;; Bbox height (rows)
             (sh (+ 1 (- sr2 sr1)))
             ;; Bbox width (cols)
             (sw (+ 1 (- sc2 sc1)))
             (hole-r1
              (let loop ((r sr1))
                (cond
                  ((<= r 0) 0)
                  ((for/and ((c (range sc1 (+ sc2 1))))
                     (let ((v (cell-at g (- r 1) c)))
                       (or (= v 0) (= v col))))
                   (loop (- r 1)))
                  (else r))))
             (hole-r2
              (let loop ((r sr2))
                (cond
                  ((>= (+ r 1) h) r)
                  ((for/and ((c (range sc1 (+ sc2 1))))
                     (let ((v (cell-at g (+ r 1) c)))
                       (or (= v 0) (= v col))))
                   (loop (+ r 1)))
                  (else r))))
             (hole-c1
              (let loop ((c sc1))
                (cond
                  ((<= c 0) 0)
                  ((for/and ((r (range sr1 (+ sr2 1))))
                     (let ((v (cell-at g r (- c 1))))
                       (or (= v 0) (= v col))))
                   (loop (- c 1)))
                  (else c))))
             (hole-c2
              (let loop ((c sc2))
                (cond
                  ((>= (+ c 1) w) c)
                  ((for/and ((r (range sr1 (+ sr2 1))))
                     (let ((v (cell-at g r (+ c 1))))
                       (or (= v 0) (= v col))))
                   (loop (+ c 1)))
                  (else c)))))
        (for*/fold ((o out))
                   ((r (range hole-r1 (+ hole-r2 1)))
                    (c (range hole-c1 (+ hole-c2 1))))
          (let* ((dr (modulo (- r sr1) sh))
                 (dc (modulo (- c sc1) sw))
                 (stamp-val (cell-at g (+ sr1 dr) (+ sc1 dc))))
            (cond
              ((= stamp-val col) (set-cell o r c col))
              (else o)))))))))