(rule!
  (let* ((key (at g 0 0))
         (obj (crop-to-content (set-cell g 0 0 0))))
    (if (= key 1)
        (rotate-cw obj)
        (if (= key 2) (rotate-180 obj) (rotate-ccw obj)))))