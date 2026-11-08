(rule!
 ;; Infer the canvas background and each hollow 9x9 compass motif. Its eight
 ;; 3x3 tiles supply inward-facing corner/edge-center tips. Those tips and the
 ;; motif's modal ground color complete the central 3x3 core. Reflect each tile
 ;; radially into the next outer position (flip each nonzero direction axis).
 ;; Multiple separated motifs are completed independently; canvas edges clip.
 (lambda (g)
  (let ()
   (define extension-scope 'rarest_tip)
   (define colors (grid-colors g))
   (define background (for/fold ((best (first colors))) ((c (in-list colors)))
     (if (> (count-color g c) (count-color g best)) c best)))
   (define motifs (objects-multicolor g background))
   (for/fold ((out g)) ((obj (in-list motifs)))
    (let ()
     (define top (obj-r1 obj))
     (define left (obj-c1 obj))
     (define values (map (lambda (p) (at g (first p) (second p))) (obj-cells obj)))
     (define ground (for/fold ((best (first (sort (remove-duplicates values) <))))
                      ((c (in-list (sort (remove-duplicates values) <))))
       (if (> (count-if (lambda (v) (= v c)) values)
              (count-if (lambda (v) (= v best)) values)) c best)))
     ;; Each record: tile row, tile column, measured inward-tip color.
     (define tiles (for*/list ((i (in-range 3)) (j (in-range 3))
                              #:unless (and (= i 1) (= j 1)))
       (list i j (at g (+ top (* 3 i) (- 2 i)) (+ left (* 3 j) (- 2 j))))))
     (define tip-values (map third tiles))
     (define (frequency color) (count-if (lambda (v) (= v color)) tip-values))
     (define minimum-frequency (apply min (map frequency (remove-duplicates tip-values))))
     (define chosen (filter (lambda (tile)
       (or (eq? extension-scope 'all) (= (frequency (third tile)) minimum-frequency))) tiles))
     (define filled (for*/fold ((acc out)) ((i (in-range 3)) (j (in-range 3)))
       (set-cell acc (+ top 3 i) (+ left 3 j) ground)))
     (define core (for/fold ((acc filled)) ((tile (in-list tiles)))
       (set-cell acc (+ top 3 (first tile)) (+ left 3 (second tile)) (third tile))))
     (for/fold ((acc core)) ((tile (in-list chosen)))
      (let ((i (first tile)) (j (second tile)))
       (for*/fold ((painted acc)) ((r (in-range 3)) (c (in-range 3)))
        (let ((rr (+ top (* 6 i) -3 r)) (cc (+ left (* 6 j) -3 c)))
         (if (and (<= 0 rr) (< rr (rows g)) (<= 0 cc) (< cc (cols g)))
          (set-cell painted rr cc
            (at g (+ top (* 3 i) (if (= i 1) r (- 2 r)))
                  (+ left (* 3 j) (if (= j 1) c (- 2 c)))))
          painted))))))))))
