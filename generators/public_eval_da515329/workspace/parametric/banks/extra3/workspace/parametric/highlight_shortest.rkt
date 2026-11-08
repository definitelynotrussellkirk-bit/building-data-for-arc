(rule!
  ;; Complete the canonical four-arm spiral, then use the completed clipped
 ;; component sizes to recolor the shortest clipped path with color 2.  Grow one arm on the unbounded lattice, preferring
 ;; a right turn, then straight, then left, while forbidding contact with any
 ;; older path cell even diagonally (except the two most recent cells).  Rotate
 ;; every accepted step by quarter turns and clip the result to the input frame.
 (lambda (g)
  (let ()
   (define directions '((-1 0) (0 1) (1 0) (0 -1)))
   (define color (first (grid-colors g 0)))
   (define points (find-color g color))
   (define top (apply min (map first points)))
   (define bottom (apply max (map first points)))
   (define left (apply min (map second points)))
   (define right (apply max (map second points)))
   (define center-r (quotient (+ top bottom) 2))
   (define center-c (quotient (+ left right) 2))
   (define arm-len (quotient (- bottom top) 2))
   (define occupied
    (for*/list ((d directions) (step (range 1 (+ arm-len 1))))
     (list (* (first d) step) (* (second d) step))))
   (define expected
    (for*/list ((d directions) (step (range 1 (+ arm-len 1))))
     (list (+ center-r (* (first d) step)) (+ center-c (* (second d) step)))))
   (unless (and (> arm-len 0) (= (- right left) (* 2 arm-len))
                (= (length points) (length expected))
                (for/and ((p points)) (member p expected)))
    (error 'spiral "expected a hollow-centered equal-arm cross"))
   (define (rotations p)
    (let loop ((n 0) (r (first p)) (c (second p)) (acc '()))
     (if (= n 4) (reverse acc)
      (loop (+ n 1) c (- r) (cons (list r c) acc)))))
   (define (safe? candidate occupied previous)
    (for*/and ((dr '(-1 0 1)) (dc '(-1 0 1)))
     (let ((q (list (+ (first candidate) dr) (+ (second candidate) dc))))
      (or (not (member q occupied)) (member q previous)))))
   (define head (list (- arm-len) 0))
   (define previous
    (if (= arm-len 1) (list head)
     (list (list (- (- arm-len 1)) 0) head)))
   (define completed
    (let loop ((head head) (heading 0) (previous previous)
               (occupied occupied) (out g) (turns-outside 0))
    (define choices (list (modulo (+ heading 1) 4) heading (modulo (+ heading 3) 4)))
    (define direction
     (for/first ((d choices)
                 #:when (let* ((delta (list-ref directions d))
                               (candidate (list (+ (first head) (first delta))
                                                (+ (second head) (second delta)))))
                          (safe? candidate occupied previous))) d))
    (unless direction (error 'spiral "no legal continuation"))
    (define delta (list-ref directions direction))
    (define candidate (list (+ (first head) (first delta))
                            (+ (second head) (second delta))))
    (define proposals (rotations candidate))
    (define visible?
     (for/or ((p proposals))
      (in-bounds? (+ center-r (first p)) (+ center-c (second p)) (rows g) (cols g))))
    (define next-out
     (for/fold ((canvas out)) ((p proposals))
      (let ((r (+ center-r (first p))) (c (+ center-c (second p))))
       (if (in-bounds? r c (rows g) (cols g)) (set-cell canvas r c color) canvas))))
    (define next-turns
     (cond (visible? 0)
           ((= direction (modulo (+ heading 1) 4)) (+ turns-outside 1))
           ((not (= direction heading)) (- turns-outside 1))
           (else turns-outside)))
    (if (and (not visible?) (>= next-turns 4)) out
     (loop candidate direction
           (if (= (length previous) 1) (append previous (list candidate))
               (list (second previous) candidate))
           (append occupied proposals) next-out next-turns))))
   (define groups (objects completed 0))
   (define selected
    (for/fold ((best (first groups))) ((o (rest groups)))
     (if (< (obj-size o) (obj-size best)) o best)))
   (for/fold ((canvas completed)) ((p (obj-cells selected)))
    (set-cell canvas (first p) (second p) 2))))))
