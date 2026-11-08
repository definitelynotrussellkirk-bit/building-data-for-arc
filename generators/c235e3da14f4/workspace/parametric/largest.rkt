(rule! (lambda (g)
         (let* ((objs (objects g 2))
                (largest (pick-max objs obj-size)))
           (crop-object g largest))))
