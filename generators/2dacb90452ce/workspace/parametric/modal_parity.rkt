(rule! (lambda (g)
  (let* ((modal-color (mode g))
         (modal-count
          (length
           (filter (lambda (v) (= v modal-color))
                   (apply append g))))
         (factor (if (= (modulo modal-count 2) 1) 3 2)))
    (upscale g factor))))
