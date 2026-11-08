(rule!
 ;; The framed row contains a guide, two source panels, and a blank target.
 ;; In the guide, the largest 8-connected component is an edge-to-edge divider;
 ;; the remaining same-colour component marks one of the divider's 4-connected
 ;; regions. The second panel supplies that marked region and wins conflicts on
 ;; the divider; the third panel supplies every other region.
 (lambda (g)
  (let ()
   (define marker-source 'second)
   (define ph (- h 2))
   (define pw (quotient (- w 5) 4))
   (define starts (for/list ((i (range 4))) (+ 1 (* i (+ pw 1)))))
   (define s0 (first starts))
   (define s1 (second starts))
   (define s2 (third starts))
   (define s3 (fourth starts))
   (define bg (at g 1 s3))
   (define guide-mask
    (build-grid ph pw (r c) (if (= (at g (+ r 1) (+ s0 c)) bg) 0 1)))
   (define guide-components (objects-8 guide-mask 0))
   (define divider-object (pick-max guide-components obj-size))
   (define divider (obj-cells divider-object))
   (define marker
    (for/first ((o guide-components) #:unless (equal? (obj-cells o) divider))
     (first (obj-cells o))))
   (define region-mask
    (build-grid ph pw (r c) (if (member (list r c) divider) 0 1)))
   (define regions (objects region-mask 0))
   (define marked-region
    (obj-cells (for/first ((o regions) #:when (member marker (obj-cells o))) o)))
   (define primary-start (if (eq? marker-source 'second) s1 s2))
   (define secondary-start (if (eq? marker-source 'second) s2 s1))
   (build-grid h w (r c)
    (if (and (<= 1 r) (< r (- h 1)) (<= s3 c) (< c (+ s3 pw)))
     (let* ((lr (- r 1)) (lc (- c s3)) (p (list lr lc))
            (a (at g r (+ primary-start lc)))
            (b (at g r (+ secondary-start lc))))
      (cond ((member p divider) (if (= a bg) b a))
            ((member p marked-region) a)
            (else b)))
     (at g r c))))))
