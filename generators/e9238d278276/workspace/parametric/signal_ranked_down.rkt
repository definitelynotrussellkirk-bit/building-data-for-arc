(rule!
 (lambda (g)
   (let ((dummy 0))
     (define (column-values c)
       (filter
        (lambda (value) (not (= value 0)))
        (map (lambda (r) (at g r c)) (range 0 (rows g)))))
     (let* ((h (rows g))
            (w (cols g))
            (active
             (filter
              (lambda (c) (not (empty? (column-values c))))
              (range 0 w)))
            (signal-col
             (first
              (filter
               (lambda (c)
                 (all? (lambda (value) (= value 9)) (column-values c)))
               active)))
            (rank (length (column-values signal-col)))
            (payload
             (filter (lambda (c) (not (= c signal-col))) active))
            (target (nth payload (- rank 1)))
            (values (column-values target))
            (up (gravity g "up"))
            (cleared
             (for/fold ((out up)) ((r (in-list (range 0 h))))
               (set-cell out r target 0))))
       (for/fold
        ((out cleared))
        ((value (in-list values))
         (r (in-list (range (- h (length values)) h))))
        (set-cell out r target value))))))
