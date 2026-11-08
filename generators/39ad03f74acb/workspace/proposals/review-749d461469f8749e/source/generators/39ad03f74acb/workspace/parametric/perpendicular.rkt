(rule!
  (let* ((segments (filter (lambda (o) (= (obj-color o) 1)) (objects g 0)))
         (controller (pick-max segments obj-size))
         (controller-horizontal (> (obj-w controller) (obj-h controller))))
    (grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (let ((left (= (safe-at g r (- c 1) 0) 1))
              (right (= (safe-at g r (+ c 1) 0) 1))
              (up (= (safe-at g (- r 1) c 0) 1))
              (down (= (safe-at g (+ r 1) c 0) 1)))
          (if (and (= (at g r c) 1)
                   (if controller-horizontal
                       (and up down (not left) (not right))
                       (and left right (not up) (not down))))
              2
              (at g r c)))))))
