(rule! (lambda (g)
  (stack-grids 'vertical
    (list
      (stack-grids 'horizontal (list g (rotate-ccw g)))
      (stack-grids 'horizontal (list (rotate-cw g) (rotate-180 g)))))))
