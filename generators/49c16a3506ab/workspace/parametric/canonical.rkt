(rule! (lambda (g)
  ;; Each color has a solid 3x3 block in one corner (bg=6). Scattered same-color
  ;; cells slide onto the block: row-band cells slide horizontally, col-band cells
  ;; vertically, diagonal cells diagonally toward the corner, stopping adjacent to
  ;; the block edge (compositional slide, not a memorized patch table).
  (let* ((H (rows g)) (W (cols g)) (bg 6)
         (palette (filter (lambda (c) (not (= c bg))) (grid-colors g))))
    (foldl
      (lambda (col acc)
        (let* ((corners (list (list 0 0) (list 0 (- W 3)) (list (- H 3) 0) (list (- H 3) (- W 3))))
               (corner (findf
                         (lambda (rc)
                           (andmap (lambda (dr)
                                     (andmap (lambda (dc) (= (cell-at g (+ (first rc) dr) (+ (second rc) dc)) col)) (list 0 1 2)))
                                   (list 0 1 2)))
                         corners))
               (r0 (first corner)) (c0 (second corner))
               (hdir (if (= c0 0) -1 1))
               (vdir (if (= r0 0) -1 1))
               (inblock? (lambda (r c) (and (>= r r0) (<= r (+ r0 2)) (>= c c0) (<= c (+ c0 2)))))
               (scattered (filter (lambda (rc) (not (inblock? (first rc) (second rc)))) (find-color g col))))
          (foldl
            (lambda (rc a)
              (let* ((r (first rc)) (c (second rc))
                     (rowband (and (>= r r0) (<= r (+ r0 2))))
                     (colband (and (>= c c0) (<= c (+ c0 2))))
                     (dr (if colband vdir (if rowband 0 vdir)))
                     (dc (if rowband hdir (if colband 0 hdir))))
                (letrec ((slide (lambda (rr cc)
                                  (let ((nr (+ rr dr)) (nc (+ cc dc)))
                                    (if (or (< nr 0) (>= nr H) (< nc 0) (>= nc W) (inblock? nr nc))
                                        (list rr cc)
                                        (slide nr nc))))))
                  (let* ((dest (slide r c))
                         (a2 (set-cell a r c bg)))
                    (set-cell a2 (first dest) (second dest) col)))))
            acc scattered)))
      g palette))))