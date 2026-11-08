(rule! (lambda (g)
  (let ([objs (objects-8 g 0)])
    (if (empty? objs)
        g
        (crop-object g (argmax obj-size objs))))))
