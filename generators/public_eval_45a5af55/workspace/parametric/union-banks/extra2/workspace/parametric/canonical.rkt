(rule!
 ;; Read the color of every monochrome row except the duplicated last row.
 ;; Use those colors, from outside to inside, as concentric square layers.
 (lambda (g)
  (let ()
   (define crop-inside #f)
   (define n (- (rows g) 1))
   (define colors (map (lambda (r) (at g r 0)) (range 0 n)))
   (define side (* 2 n))
   (define full
    (build-list side
     (lambda (r)
      (build-list side
       (lambda (c) (nth colors (min r c (- side 1 r) (- side 1 c))))))))
   (if crop-inside
    (let* ((depths
            (filter
             (lambda (d)
              (= 1 (count-if (lambda (x) (= x (nth colors d))) colors)))
             (range 0 n)))
           (marker (first depths))
           (start (+ marker 1))
           (stop (- side marker 2)))
     (subgrid full start start stop stop))
    full))))
