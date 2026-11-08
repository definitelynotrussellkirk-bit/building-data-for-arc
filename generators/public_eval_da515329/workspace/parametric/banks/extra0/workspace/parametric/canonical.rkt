(rule!
 ;; Complete four interleaved clockwise square spirals from equal radial spokes.
 ;; Infer their common center and spoke radius; the one-cell seed extends to two.
 ;; Each elbow consists of a growing run, a radius-dependent inward notch, and
 ;; an outward continuation. Continue in the plane, THEN clip to the canvas:
 ;; an arm may leave the canvas and re-enter as a disconnected edge fragment.
 (lambda (g)
  (let ()
   (define output-policy "all_paths")
   (define seeds (filter (lambda (p) (not (= (at g (first p) (second p)) 0))) (grid-positions g)))
   (define box (bbox-of-cells seeds))
   (define cr (/ (+ (first box) (third box)) 2))
   (define cc (/ (+ (second box) (fourth box)) 2))
   (define radius (max 2 (/ (- (third box) (first box)) 2)))
   (define color (at g (first (first seeds)) (second (first seeds))))
   (define (advance p dr dc n) (list (+ (first p) (* dr n)) (+ (second p) (* dc n))))
   (define (line p dr dc n)
    (filter (lambda (q) (in-bounds? (first q) (second q) h w))
     (for/list ((t (range 1 (+ n 1)))) (advance p dr dc t))))
   (define (trace p dr dc k cells)
    (if (>= k (max h w)) cells
     (let* ((long (+ 2 (* 4 k))) (er dc) (ec (- dr))
            (q (advance p dr dc long))
            (u (advance q er ec (- radius 2)))
            (v (advance u dr dc radius)))
      (trace v er ec (+ k 1)
       (append cells (line p dr dc long) (line q er ec (- radius 2)) (line u dr dc radius))))))
   (define arms
    (for/list ((d (list (list -1 0) (list 0 1) (list 1 0) (list 0 -1))))
     (let* ((dr (first d)) (dc (second d)) (center (list cr cc))
            (head (advance center dr dc radius)))
      (trace head dc (- dr) 0 (line center dr dc radius)))))
   (define completed (recolor-cells g (apply append arms) color))
   (define groups (objects completed 0))
   (define selected
    (cond
     ((equal? output-policy "all_paths") '())
     ((equal? output-policy "smallest") (obj-cells (pick-min groups obj-size)))
     ((equal? output-policy "first") (obj-cells (first groups)))
     ((equal? output-policy "last") (obj-cells (last groups)))
     ((equal? output-policy "bbox") (obj-cells (pick-max groups (lambda (o) (* (obj-h o) (obj-w o))))))
     ((equal? output-policy "north_seed")
      (obj-cells (for/first ((o groups) #:when (member (list (- cr 1) cc) (obj-cells o))) o)))
     ((equal? output-policy "whole_arm") (pick-max arms length))
     (else (obj-cells (pick-max groups obj-size)))))
   (recolor-cells completed selected 2))))
