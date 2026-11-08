(rule!
 ;; A marker enters only between an equal-color pair of rails. Move forward
 ;; through orange. Adaptive guidance is replaced by each newly observed
 ;; equal-color flank pair. Turn at a matching wall only if exactly one
 ;; perpendicular neighbor is open; stop at other colors, ambiguity or edge.
 ;; Trace against immutable input, then clear sources and paint endpoints.
 ;; Guidance: adaptive; ablation: none.
 (lambda (g)
  (let ()
   (define (wall? v) (and (not (= v 6)) (not (= v 7))))
   (define (entrance r)
    (let ((column (for/first ((c (range 1 w))
                         #:when (or (not (= (at g (- r 1) c) 7))
                                    (not (= (at g (+ r 1) c) 7))
                                    (not (= (at g r c) 7)))) c)))
     (if (and column (= (at g r column) 7))
      (let ((a (at g (- r 1) column)) (b (at g (+ r 1) column))) (if (and (= a b) (not (= a 6)) (not (= a 7))) a #f)) #f)))
   (define (trace source initial)
    (let loop ((rr source) (cc 0) (dr 0) (dc 1) (color initial) (seen '()) (trail '()))
     (let* ((state (list rr cc dr dc color))
            (here (list rr cc)) (next-trail (cons here trail))
            (finish (list source rr cc next-trail))
            (left (safe-at g (- rr dc) (+ cc dr) 7))
            (right (safe-at g (+ rr dc) (- cc dr) 7))
            (next-color (if (and (= left right) (not (= left 6)) (not (= left 7))) left color))
            (nr (+ rr dr)) (nc (+ cc dc)))
      (cond ((member state seen) finish)
            ((not (in-bounds? nr nc h w)) finish)
            (else
             (let ((value (at g nr nc)))
              (cond ((= value 7) (loop nr nc dr dc next-color (cons state seen) next-trail))
                    ((= value next-color)
                     (let ((options (filter
                         (lambda (delta)
                          (let ((r (+ rr (first delta))) (c (+ cc (second delta))))
                           (and (in-bounds? r c h w) (= (at g r c) 7))))
                         (list (list (- 0 dc) dr) (list dc (- 0 dr))))))
                      (if (= (length options) 1)
                       (let ((direction (first options)))
                        (if #t
                         (loop rr cc (first direction) (second direction) next-color (cons state seen) next-trail)
                         finish)) finish)))
                    (else finish))))))))
   (define all-paths
    (for/list ((r (range 1 (- h 1))) #:when (and (= (at g r 0) 6) (entrance r)))
     (trace r (entrance r))))
   (define paths all-paths)
   (define cleared (for/fold ((out g)) ((t paths)) (set-cell out (first t) 0 7)))
   (for/fold ((out cleared)) ((t paths))
    (for/fold ((next out)) ((p (list (list (second t) (third t))))) (set-cell next (first p) (second p) 6))))))
