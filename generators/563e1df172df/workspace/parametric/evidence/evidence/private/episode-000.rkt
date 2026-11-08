(rule!
 (lambda (g)
   ;; Red is the start and green is the destination.  The elbow belongs on
   ;; red's row and green's column, so the horizontal arm is drawn first.
   (define red (first (find-color g 2)))
   (define green (first (find-color g 3)))
   (define rr (first red))
   (define rc (second red))
   (define gr (first green))
   (define gc (second green))
   (define cmin (min rc gc))
   (define cmax (max rc gc))
   (define rmin (min rr gr))
   (define rmax (max rr gr))
   ;; Paint the horizontal arm while preserving the red endpoint.
   (define with-row
     (reduce (lambda (out c)
               (if (= c rc) out (set-cell out rr c 8)))
             g
             (range cmin (+ cmax 1))))
   ;; Paint the vertical arm while preserving the green endpoint.
   (reduce (lambda (out r)
             (if (= r gr) out (set-cell out r gc 8)))
           with-row
           (range rmin (+ rmax 1)))))