(rule!
 ;; Dock each black glyph against the gray divider, without changing its rows
 ;; in divider-normalized coordinates. Closed magenta pockets signal only at
 ;; positions exactly one black boundary cell behind the divider. Paint those
 ;; rows red beyond the divider; open cavities and buried pockets do not signal.
 ;; Normalize horizontal/reversed layouts before applying the same geometry.
 ;; The alternative retains only the uniquely largest exposed pocket by area.
 (lambda (g)
   (let ()
     (define signal-policy "all_exposed")
     (define vertical
       (filter (lambda (c) (for/and ((r (range h))) (= (at g r c) 5))) (range w)))
     (define turned (null? vertical))
     (define upright (if turned (transpose g) g))
     (define divider0
       (first (filter (lambda (c) (for/and ((r (range (rows upright)))) (= (at upright r c) 5)))
                      (range (cols upright)))))
     (define flipped (for/or ((p (find-color upright 0))) (> (second p) divider0)))
     (define board (if flipped (flip-lr upright) upright))
     (define nr (rows board))
     (define nc (cols board))
     (define wall (if flipped (- nc 1 divider0) divider0))
     (define black (filter (lambda (obj) (= (obj-color obj) 0)) (objects board 6)))
     (define originals (map obj-cells black))
     (define moved
       (for/list ((obj black))
         (define dc (- wall 1 (obj-c2 obj)))
         (for/list ((p (obj-cells obj))) (list (first p) (+ dc (second p))))))
     (define docked
       (for/fold ((out (recolor board 0 6))) ((points moved)) (recolor-cells out points 0)))
     (define (collect-pockets shapes)
       (apply append
         (for/list ((points shapes))
           (define mask (recolor-cells (empty-grid nr nc 6) points 0))
           (for/list ((region (find-0-regions mask 6))
                      #:unless (for/or ((p region))
                                 (or (= (first p) 0) (= (first p) (- nr 1))
                                     (= (second p) 0) (= (second p) (- nc 1)))))
             (list region (length points))))))
     (define pockets (collect-pockets moved))
     (define (exposed? pocket)
       (for/or ((p (first pocket))) (= (second p) (- wall 2))))
     (define exposed
       (filter exposed? (if (equal? signal-policy "before_docking") (collect-pockets originals) pockets)))
     (define (height-of pocket)
       (+ 1 (- (apply max (map first (first pocket))) (apply min (map first (first pocket))))))
     (define (width-of pocket)
       (+ 1 (- (apply max (map second (first pocket))) (apply min (map second (first pocket))))))
     (define chosen
       (cond
         [(equal? signal-policy "all_holes") pockets]
         [(equal? signal-policy "largest_any")
          (if (null? pockets) '() (list (pick-max pockets (lambda (p) (length (first p))))))]
         [(null? exposed) '()]
         [(equal? signal-policy "all_exposed") exposed]
         [(equal? signal-policy "first_exposed") (list (first exposed))]
         [(equal? signal-policy "last_exposed") (list (last exposed))]
         [(equal? signal-policy "median_exposed") (list (list-ref exposed (quotient (length exposed) 2)))]
         [(equal? signal-policy "smallest_exposed") (list (pick-min exposed (lambda (p) (length (first p)))))]
         [(equal? signal-policy "largest_bbox") (list (pick-max exposed (lambda (p) (* (height-of p) (width-of p)))))]
         [(equal? signal-policy "tallest") (list (pick-max exposed height-of))]
         [(equal? signal-policy "widest") (list (pick-max exposed width-of))]
         [(equal? signal-policy "largest_body") (list (pick-max exposed second))]
         [else (list (pick-max exposed (lambda (p) (length (first p)))))]))
     (define signal-rows
       (if (equal? signal-policy "open_column")
           (filter (lambda (r) (and (= (at docked r (- wall 1)) 0) (= (at docked r (- wall 2)) 6))) (range nr))
           (remove-duplicates
             (for*/list ((pocket chosen) (p (first pocket))
                         #:when (or (equal? signal-policy "all_holes") (= (second p) (- wall 2))))
               (first p)))))
     (define signalled
       (for*/fold ((out docked)) ((r signal-rows) (c (range (+ wall 1) nc))) (set-cell out r c 2)))
     (define unflipped (if flipped (flip-lr signalled) signalled))
     (if turned (transpose unflipped) unflipped))))
