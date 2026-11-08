(rule!
 ;; A gray wire selects two center-aligned beads. Diagonal wire links count
 ;; unless a gray cardinal corner already joins the same pixels. Recover both
 ;; leaves, assign distinct aligned beads whose center colors name donor beads,
 ;; and copy each donor's center color into its receiver. Erase all other beads;
 ;; gray wire pixels remain unchanged. Uniform and boundary-clipped beads work.
 ;; The follow-chain variant repeatedly resolves the new color in the ORIGINAL
 ;; bead dictionary, stopping on a missing key or the first repeated color.
 (lambda (g)
   (let ()
     (define transfer-policy "one_hop")
     (define wire (find-color g 5))
     (define (connected p q)
       (let ((dr (- (first q) (first p))) (dc (- (second q) (second p))))
         (and (not (equal? p q)) (<= (abs dr) 1) (<= (abs dc) 1)
              (or (= dr 0) (= dc 0)
                  (and (not (member (list (first q) (second p)) wire))
                       (not (member (list (first p) (second q)) wire)))))))
     (define ends (filter (lambda (p) (= 1 (length (filter (lambda (q) (connected p q)) wire)))) wire))
     (define raw (objects (grid-from-fn h w (lambda (r c) (if (member (at g r c) '(0 5)) 0 1))) 0))
     (define beads
       (for/list ((o raw))
         (let* ((body (mode-list (map (lambda (p) (at g (first p) (second p))) (obj-cells o))))
                (different (filter (lambda (p) (not (= (at g (first p) (second p)) body))) (obj-cells o)))
                (center (if (null? different)
                            (list (quotient (+ (obj-r1 o) (obj-r2 o)) 2)
                                  (quotient (+ (obj-c1 o) (obj-c2 o)) 2))
                            (first different))))
           (list body center (at g (first center) (second center)) (obj-cells o)))))
     (define body-colors (map first beads))
     (define (candidates p)
       (filter
        (lambda (b)
          (and (member (third b) body-colors)
               (or (= (first p) (first (second b))) (= (second p) (second (second b))))
               (for/or ((q (fourth b)))
                 (= 1 (+ (abs (- (first p) (first q))) (abs (- (second p) (second q))))))))
        beads))
     (define assignments
       (for*/list ((a (candidates (first ends))) (b (candidates (second ends)))
                   #:when (not (= (first a) (first b))))
         (list a b)))
     (define selected (first assignments))
     (define (resolve value budget seen)
       (let ((donor (find-first (lambda (b) (= (first b) value)) beads)))
         (if (or (= budget 0) (not donor) (member value seen)) value
             (resolve (third donor) (- budget 1) (cons value seen)))))
     (define steps
       (cond ((equal? transfer-policy "follow_chain") (+ 1 (length beads)))
             ((equal? transfer-policy "two_hops") 2)
             ((equal? transfer-policy "three_hops") 3)
             ((equal? transfer-policy "raw_center") 0)
             (else 1)))
     (define blank (grid-from-fn h w (lambda (r c) (if (= (at g r c) 5) 5 0))))
     (for/fold ((out blank)) ((b selected))
       (let* ((copied (for/fold ((acc out)) ((p (fourth b)))
                        (set-cell acc (first p) (second p) (at g (first p) (second p)))))
              (center (second b))
              (value (resolve (third b) steps '())))
         (set-cell copied (first center) (second center) value))))))
