
(rule!
 ;; Two objects: a solid rectangle WALL and a creature made of a solid
 ;; BODY with a tail sticking out one side. The tail points AWAY from
 ;; travel: the body slides toward the wall until flush against it, and
 ;; the tail is consumed. Background elsewhere unchanged.
 (lambda (g)
   (let ()
     (define objs (objects g 0))
     (define wall (find-first solid-rect? objs))
     (define creature
       (find-first (lambda (o) (not (solid-rect? o))) objs))
     (define cells (obj-cells creature))
     (define body  ;; largest solid rectangle inside the creature
       (rest
        (for*/fold ((best (list 0 0 0 0 0)))
                   ((r1 (range (obj-r1 creature)
                               (+ (obj-r2 creature) 1)))
                    (r2 (range (obj-r1 creature)
                               (+ (obj-r2 creature) 1)))
                    (c1 (range (obj-c1 creature)
                               (+ (obj-c2 creature) 1)))
                    (c2 (range (obj-c1 creature)
                               (+ (obj-c2 creature) 1))))
          (if (and (<= r1 r2) (<= c1 c2)
                   (> (* (+ 1 (- r2 r1)) (+ 1 (- c2 c1))) (first best))
                   (all? (lambda (p) (member p cells))
                         (positions-in-rect r1 c1 r2 c2)))
              (list (* (+ 1 (- r2 r1)) (+ 1 (- c2 c1))) r1 r2 c1 c2)
              best))))
     (define br1 (first body))
     (define br2 (second body))
     (define bc1 (third body))
     (define bc2 (fourth body))
     (define tail  ;; creature cells outside the body rect
       (filter (lambda (p) (not (and (>= (first p) br1)
                                     (<= (first p) br2)
                                     (>= (second p) bc1)
                                     (<= (second p) bc2))))
               cells))
     (define dr (cond ((any? (lambda (p) (< (first p) br1)) tail) -1)
                      ((any? (lambda (p) (> (first p) br2)) tail) 1)
                      (else 0)))
     (define dc (cond ((any? (lambda (p) (< (second p) bc1)) tail) -1)
                      ((any? (lambda (p) (> (second p) bc2)) tail) 1)
                      (else 0)))
     (define steps  ;; distance until flush against the wall
       (cond ((> dc 0) (- (obj-c1 wall) 1 bc2))
             ((< dc 0) (- bc1 (+ (obj-c2 wall) 1)))
             ((> dr 0) (- (obj-r1 wall) 1 br2))
             ((< dr 0) (- br1 (+ (obj-r2 wall) 1)))
             (else 0)))
     (paint-cells (erase-cells g cells 0)
                  (positions-in-rect (+ br1 (* dr steps))
                                     (+ bc1 (* dc steps))
                                     (+ br2 (* dr steps))
                                     (+ bc2 (* dc steps)))
                  (obj-color creature)))))
