(rule!
  (let* ((objs (sort (objects g 0)
                     (lambda (a b)
                       (if (= (obj-r1 a) (obj-r1 b))
                           (< (obj-c1 a) (obj-c1 b))
                           (< (obj-r1 a) (obj-r1 b))))))
         (widths (map obj-w objs))
         (n (length widths)))
    (grid-from-fn n n
      (lambda (r c)
        (let ((a (list-ref widths r)) (b (list-ref widths c)))
          (cond [(= a b) 1] [(> a b) 2] [else 3]))))))