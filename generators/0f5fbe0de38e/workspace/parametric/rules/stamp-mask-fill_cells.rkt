(rule!
 ;; A multicolor TEMPLATE (majority fill color + 2 marker cells of other
 ;; colors) shows a shape at unit scale. Loose marker-colored objects
 ;; pair up (nearest gap first, different colors): each pair anchors a
 ;; scaled-up ghost of the template under some rotation/flip — the two
 ;; markers must land exactly on the two objects. Paint the ghost's
 ;; fill cells (scaled to the objects' size) onto the background.
 (lambda (g)
   (let ()
     (define bg (mode g -1))
     (define (obj-colors obj)
       (unique (map (lambda (p) (at g (first p) (second p)))
                    (obj-cells obj))))
     (define template
       (first (sort-by (filter (lambda (o) (>= (length (obj-colors o)) 3))
                               (objects-multicolor g bg))
                       (lambda (o) (+ (* 1000 (obj-size o))
                                      (* 30 (obj-r1 o)) (obj-c1 o))))))
     (define th (obj-h template))
     (define tw (obj-w template))
     (define fill-color
       (mode-list (map (lambda (p) (at g (first p) (second p)))
                       (obj-cells template))))
     (define template-cells  ;; (r c v) normalized to the template bbox
       (map (lambda (p) (list (- (first p) (obj-r1 template))
                              (- (second p) (obj-c1 template))
                              (at g (first p) (second p))))
            (obj-cells template)))
     (define marker-cells
       (filter (lambda (p) (not (= (third p) fill-color))) template-cells))
     (define fill-cells
       (filter (lambda (p) (= (third p) fill-color)) template-cells))
     (define marker-objs
       (sort-by (filter (lambda (o)
                          (and (not (for/or ((p (obj-cells o)))
                                      (member p (obj-cells template))))
                               (member (obj-color o)
                                       (filter (lambda (c)
                                                 (not (= c fill-color)))
                                               (obj-colors template)))))
                        (objects g bg))
                (lambda (o) (+ (* 1000 (obj-r1 o)) (obj-c1 o)))))
     (define (gap-dist a b)  ;; bbox gap, manhattan
       (+ (max 0 (- (max (obj-r1 a) (obj-r1 b))
                    (min (obj-r2 a) (obj-r2 b)) 1))
          (max 0 (- (max (obj-c1 a) (obj-c1 b))
                    (min (obj-c2 a) (obj-c2 b)) 1))))
     (define pairs  ;; greedy nearest-first, different colors, each used once
       (first
        (foldl (lambda (cand state)
                 (let ((i (second cand)) (j (third cand)))
                   (if (or (member i (second state))
                           (member j (second state)))
                       state
                       (list (append (first state)
                                     (list (list (nth marker-objs i)
                                                 (nth marker-objs j))))
                             (append (second state) (list i j))))))
               (list (list) (list))
               (sort-by (for*/list ((i (range 0 (length marker-objs)))
                                    (j (range (+ i 1)
                                              (length marker-objs)))
                                    #:when (not (= (obj-color
                                                    (nth marker-objs i))
                                                   (obj-color
                                                    (nth marker-objs j)))))
                          (list (gap-dist (nth marker-objs i)
                                          (nth marker-objs j))
                                i j))
                        first))))
     (define (xform cell t)  ;; the 8 dihedral images of a template cell
       (let ((r (first cell)) (c (second cell)))
         (cond ((zero? t) (list r c))
               ((= t 1) (list c (- th 1 r)))
               ((= t 2) (list (- th 1 r) (- tw 1 c)))
               ((= t 3) (list (- tw 1 c) r))
               ((= t 4) (list r (- tw 1 c)))
               ((= t 5) (list (- th 1 r) c))
               ((= t 6) (list c r))
               (else (list (- tw 1 c) (- th 1 r))))))
     (define (placement-at t asg a)  ;; anchor if both markers agree
       (let* ((ms (map (lambda (m) (xform m t)) marker-cells))
              (sh (obj-h a)) (sw (obj-w a))
              (anchor (lambda (m o) (list (- (obj-r1 o) (* (first m) sh))
                                          (- (obj-c1 o) (* (second m) sw)))))
              (s1 (anchor (first ms) (first asg)))
              (s2 (anchor (second ms) (second asg))))
         (and (equal? s1 s2)
              (list (first s1) (second s1)
                    (map (lambda (p) (xform p t)) fill-cells)))))
     (define (find-placement a b)
       (and (= (obj-h a) (obj-h b)) (= (obj-w a) (obj-w b))
            (find-first (lambda (x) x)
                        (for*/list ((t (range 0 8))
                                    (asg (list (list a b) (list b a))))
                          (placement-at t asg a)))))
     (define (paint-fill out placement a)
       (if placement
           (let ((sr (first placement)) (sc (second placement))
                 (sh (obj-h a)) (sw (obj-w a)))
             (for*/fold ((acc out))
                        ((p (third placement))
                         (r (range (+ sr (* (first p) sh))
                                   (+ sr (* (+ (first p) 1) sh))))
                         (c (range (+ sc (* (second p) sw))
                                   (+ sc (* (+ (second p) 1) sw)))))
               (if (and (in-bounds? r c h w) (= (at acc r c) bg))
                   (set-cell acc r c fill-color)
                   acc)))
           out))
     (for/fold ((out g)) ((pair (in-list pairs)))
       (paint-fill out (find-placement (first pair) (second pair))
                   (first pair))))))