(rule!
 ;; Locate complete 9x9 rings of eight 3x3 tiles against the modal background.
 ;; Reflect the eight tiles outward across their radial sides/corners; clip
 ;; only outside the canvas. Inward-facing tips reconstruct the missing
 ;; center tile, whose middle uses the ring's modal nonbackground color.
 (lambda (g)
   (let ()
     (define bg (mode g -1))
     (define os (objects-multicolor g bg))
     (define directions (filter (lambda (d) (or (not (= (first d) 0)) (not (= (second d) 0))))
                                (for*/list ((dr '(-1 0 1)) (dc '(-1 0 1))) (list dr dc))))
     (define stage-a
       (for/fold ((out g)) ((o os))
         (let* ((r0 (obj-r1 o)) (c0 (obj-c1 o))
                (base (mode (subgrid g r0 c0 (+ r0 8) (+ c0 8)) bg))
                (reflected
                 (for/fold ((canvas out)) ((d directions))
                   (let* ((dr (first d)) (dc (second d))
                          (sr (+ r0 (* 3 (+ dr 1)))) (sc (+ c0 (* 3 (+ dc 1))))
                          (tr (+ r0 (* 3 (+ (* 2 dr) 1)))) (tc (+ c0 (* 3 (+ (* 2 dc) 1))))
                          (copied
                           (for*/fold ((paint canvas)) ((i (range 3)) (j (range 3)))
                             (let ((r (+ tr i)) (c (+ tc j)))
                               (if (in-bounds? r c (rows g) (cols g))
                                   (set-cell paint r c (at g (+ sr (if (= dr 0) i (- 2 i)))
                                                               (+ sc (if (= dc 0) j (- 2 j))))) paint))))
                          (ir (cond ((< dr 0) 2) ((> dr 0) 0) (else 1)))
                          (ic (cond ((< dc 0) 2) ((> dc 0) 0) (else 1))))
                     (set-cell copied (+ r0 4 dr) (+ c0 4 dc) (at g (+ sr ir) (+ sc ic)))))))
           (set-cell reflected (+ r0 4) (+ c0 4) base))))
     (for/fold ((out stage-a)) ((o os))
       (let* ((r0 (obj-r1 o)) (c0 (obj-c1 o))
              (base (mode (subgrid g r0 c0 (+ r0 8) (+ c0 8)) bg))
              (observed (filter (lambda (v) (not (= v base))) (map (lambda (p) (at g (first p) (second p))) (obj-cells o))))
              (colors (remove-duplicates observed))
              (chosen (first (sort colors
                (lambda (x y)
                  (let ((nx (count (lambda (v) (= v x)) observed))
                        (ny (count (lambda (v) (= v y)) observed)))
                    (or (> nx ny) (and (= nx ny) (< x y)))))))))
         (for*/fold ((paint out)) ((r (range (max 0 (- r0 3)) (min (rows g) (+ r0 12))))
                                   (c (range (max 0 (- c0 3)) (min (cols g) (+ c0 12)))))
           (if (= (at stage-a r c) chosen) (set-cell paint r c (if (= bg 9) 0 9)) paint)))))))
