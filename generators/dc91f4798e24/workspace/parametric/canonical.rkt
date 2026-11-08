(rule!
  (let ((dummy 0))
    (define (count-components color)
      (length (filter (lambda (o) (= (obj-color o) color)) (objects g 0))))
    (let* ((n1 (count-components 1))
           (n2 (count-components 2))
           (n3 (count-components 3))
           (ww (max 1 n1 n2 n3)))
      (grid-from-fn 3 ww
        (lambda (r c)
          (let ((cnt (cond [(= r 0) n1] [(= r 1) n2] [else n3]))
                (color (+ r 1)))
            (if (< c cnt) color 0)))))))