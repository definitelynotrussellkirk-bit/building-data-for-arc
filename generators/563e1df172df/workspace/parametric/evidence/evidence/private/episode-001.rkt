(rule!
 (lambda (g)
   ;; Red is the start and green is the destination.  The elbow belongs on
   ;; green's row and red's column, so the vertical arm is drawn first.
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
   ;; Paint the vertical arm while preserving the red endpoint.
   (define with-column
     (reduce (lambda (out r)
               (if (= r rr) out (set-cell out r rc 8)))
             g
             (range rmin (+ rmax 1))))
   ;; Paint the horizontal arm while preserving the green endpoint.
   (reduce (lambda (out c)
             (if (= c gc) out (set-cell out gr c 8)))
           with-column
           (range cmin (+ cmax 1)))))