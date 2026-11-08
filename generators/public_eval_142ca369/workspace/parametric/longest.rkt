(rule!
 ;; L triominoes launch diagonal rays away from their two arms.
 ;; A singleton or three-cell straight mirror reflects at the adjacent
 ;; center on its approached side; the bounce cell takes the mirror color.
 ;; Read mirrors from the original input, never from newly drawn rays.
 ;; Preserve gadget cells. Row-major launchers overwrite earlier beam pixels.
 ;; Repeated position/direction states terminate closed paths.
 (lambda (g)
  (let ()
   (define longest? #t)
   (define obs (objects g 0))
   (define sources (filter (lambda (o) (and (= (obj-size o) 3) (= (obj-h o) 2) (= (obj-w o) 2))) obs))
   (define mirrors
    (for/list ((o obs) #:when
       (or (= (obj-size o) 1)
           (and (= (obj-size o) 3) (or (= (obj-h o) 1) (= (obj-w o) 1)))))
     (list (/ (+ (obj-r1 o) (obj-r2 o)) 2)
           (/ (+ (obj-c1 o) (obj-c2 o)) 2)
           (cond ((= (obj-size o) 1) 2) ((= (obj-h o) 1) 0) (else 1))
           (obj-color o))))
   (define (walk r c dr dc tint leg seen)
    (define state (list r c dr dc))
    (if (or (not (in-bounds? r c (rows g) (cols g))) (member state seen)) '()
     (if (not (= (at g r c) 0)) '()
      (let ()
       (define hm (for/first ((m mirrors) #:when
         (and (= (first m) (+ r dr)) (= (second m) c)
              (not (= (list-ref m 2) 1)))) m))
       (define vm (for/first ((m mirrors) #:when
         (and (= (first m) r) (= (second m) (+ c dc))
              (not (= (list-ref m 2) 0)))) m))
       (define hit (if hm hm vm))
       (define nd-r (if hm (- dr) dr))
       (define nd-c (if (and vm (not hm)) (- dc) dc))
       (define color (if hit (list-ref hit 3) tint))
       (define next-leg (if hit (+ leg 1) leg))
       (cons (list r c color next-leg)
          (walk (+ r nd-r) (+ c nd-c) nd-r nd-c color next-leg (cons state seen)))))))
   (for/fold ((out g)) ((source sources))
    (define elbow (for/first ((p (obj-cells source)) #:when
      (= (count-if (lambda (q) (= (+ (abs (- (first p) (first q)))
                                     (abs (- (second p) (second q)))) 1))
                   (obj-cells source)) 2)) p))
    (define dr (if (= (first elbow) (obj-r1 source)) -1 1))
    (define dc (if (= (second elbow) (obj-c1 source)) -1 1))
    (define path (walk (+ (first elbow) dr) (+ (second elbow) dc) dr dc (obj-color source) 0 '()))
    (define legs (remove-duplicates (map (lambda (p) (list-ref p 3)) path)))
    (define selected (if (null? legs) -1 (pick-max legs (lambda (k) (count-if (lambda (p) (= (list-ref p 3) k)) path)))))
    (paint-cells out
       (for/list ((p path) #:when (or (not longest?) (= (list-ref p 3) selected)))
        (list (first p) (second p) (list-ref p 2))))))))
