(rule!
  (let* ((objs (sort (objects g 0)
                     (lambda (a b)
                       (if (= (obj-r1 a) (obj-r1 b))
                           (< (obj-c1 a) (obj-c1 b))
                           (< (obj-r1 a) (obj-r1 b))))))
         (ranked (sort objs
                       (lambda (a b)
                         (cond [(> (obj-h a) (obj-h b)) #t]
                               [(< (obj-h a) (obj-h b)) #f]
                               [(= (obj-r1 a) (obj-r1 b))
                                (< (obj-c1 a) (obj-c1 b))]
                               [else (< (obj-r1 a) (obj-r1 b))]))))
         (pivot-width (obj-w (first ranked)))
         (scores (map (lambda (o) (abs (- (obj-w o) pivot-width))) objs))
         (n (length scores)))
    (grid-from-fn n n
      (lambda (r c)
        (let ((a (list-ref scores r)) (b (list-ref scores c)))
          (cond [(= a b) 1] [(> a b) 2] [else 3]))))))
