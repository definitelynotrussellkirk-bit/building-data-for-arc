(rule! (lambda (g)
  (stack-grids 'vertical
    (list
      (stack-grids 'horizontal (list g (rotate-cw g)))
      (stack-grids 'horizontal (list (rotate-ccw g) (rotate-180 g)))))))
