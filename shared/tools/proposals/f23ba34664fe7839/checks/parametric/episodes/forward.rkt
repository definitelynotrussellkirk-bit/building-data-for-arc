(rule!
 ;; A framed panel (blue border) has four distinct interior corner
 ;; colors; scattered dots outside repeat those colors at the corners
 ;; of THEIR bounding box, in some orientation. Output the panel
 ;; rotated/flipped so its corners land like the dots' (missing dots
 ;; read as border blue 1).
 (lambda (g)
   (let ()
     (define bb (bbox-of-cells (find-color g 1)))
     (define pr1 (first bb)) (define pc1 (second bb))
     (define pr2 (third bb)) (define pc2 (fourth bb))
     (define panel (subgrid g pr1 pc1 pr2 pc2))
     (define ph (rows panel))
     (define pw (cols panel))
     (define A (at panel 1 1))
     (define B (at panel 1 (- pw 2)))
     (define C (at panel (- ph 2) 1))
     (define D (at panel (- ph 2) (- pw 2)))
     (define scattered
       (filter (lambda (p) (let ((r (first p)) (c (second p)))
                             (and (> (at g r c) 0)
                                  (or (< r pr1) (> r pr2)
                                      (< c pc1) (> c pc2)))))
               (grid-positions g)))
     (define sbb (bbox-of-cells scattered))
     (define (dot r c)  ;; scattered color there, else border blue
       (if (member (list r c) scattered) (at g r c) 1))
     (define signature
       (list (dot (first sbb) (second sbb))
             (dot (first sbb) (fourth sbb))
             (dot (third sbb) (second sbb))
             (dot (third sbb) (fourth sbb))))
     (define transforms  ;; (corner-signature transform), identity first
       (list (list (list A B C D) (lambda (p) p))
             (list (list B A D C) flip-lr)
             (list (list C D A B) flip-ud)
             (list (list D C B A) rotate-180)
             (list (list A C B D) transpose)
             (list (list D B C A)
                   (lambda (p) (rotate-180 (transpose p))))
             (list (list C A D B) rotate-cw)
             (list (list B D A C) rotate-ccw)))
     ((second (find-first (lambda (t) (equal? (first t) signature))
                          transforms))
      panel))))