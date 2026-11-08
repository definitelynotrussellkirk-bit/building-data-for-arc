(rule! (lambda (g)
  (let* ((objs (objects-multicolor g 0))
         (first-obj (first objs)))
    (crop-object g first-obj))))