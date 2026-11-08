(rule!
 ;; Decode the isolated symbol map around its template-colored anchor.
 ;; Map spacing encodes tile offsets, not physical stamp spacing: each
 ;; target displacement is multiplied by the template bounding-box size.
 ;; Erase the map, recolor the central template to the symbol color, and
 ;; stamp the template ink at each remote target in the original ink color.
 (lambda (g)
  (let ()
   (define holes? #f)
   (define bg (mode g -1))
   (define obs (objects g bg))
   (define shape (pick-max obs obj-size))
   (if (or (not shape) (<= (obj-size shape) 1)) g
    (let ()
     (define ink (obj-color shape))
     (define tokens (filter (lambda (o) (= (obj-size o) 1)) obs))
     (define anchors (filter (lambda (o) (= (obj-color o) ink)) tokens))
     (define marks (filter (lambda (o) (not (= (obj-color o) ink))) tokens))
     (if (or (not (= (length anchors) 1)) (null? marks)) g
      (let ()
       (define anchor (first anchors))
       (define tint (obj-color (first marks)))
       (define (gcd2 a b) (if (= b 0) a (gcd2 b (modulo a b))))
       (define (pitch coord)
        (define nums (sort (remove-duplicates (map coord tokens)) <))
        (if (< (length nums) 2) 1
         (for/fold ((v 0)) ((x (rest nums))) (gcd2 v (- x (first nums))))))
       (define pr (pitch obj-r1))
       (define pc (pitch obj-c1))
       (define sh (obj-h shape))
       (define sw (obj-w shape))
       (define rr (obj-r1 shape))
       (define cc (obj-c1 shape))
       (define cellmask
        (for*/list ((r (range sh)) (c (range sw))
          #:when (if holes? (= (at g (+ rr r) (+ cc c)) bg)
                             (= (at g (+ rr r) (+ cc c)) ink))) (list r c)))
       (define center (recolor-cells (empty-grid (rows g) (cols g) bg)
                                     (obj-cells shape) tint))
       (for/fold ((out center)) ((mark marks))
        (define tr (+ rr (* sh (/ (- (obj-r1 mark) (obj-r1 anchor)) pr))))
        (define tc (+ cc (* sw (/ (- (obj-c1 mark) (obj-c1 anchor)) pc))))
        (paint-cells out (map (lambda (p) (list (+ tr (first p)) (+ tc (second p)))) cellmask) ink)))))))))
