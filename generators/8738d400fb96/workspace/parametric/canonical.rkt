(rule!
  (let* ((shape (argmax obj-size (filter (lambda (o) (= (obj-color o) 3)) (objects g 0))))
         (a (first (find-color g 2)))
         (b (first (find-color g 1)))
         (dr (- (first b) (first a)))
         (dc (- (second b) (second a)))
         (moved (map (lambda (p) (list (+ (first p) dr) (+ (second p) dc))) (obj-cells shape))))
    (paint-cells (empty-grid h w 0) moved 8)))