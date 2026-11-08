(rule!
 ;; Four square quadrants encode size, background, and foreground tile.
 ;; Nonzero counts in the upper-left and upper-right give output height/width.
 ;; Stretch the lower-left image to that size, using floor-index nearest
 ;; neighbors. Tile the lower-right image from the output origin: zero is
 ;; transparent, every nonzero tile pixel overwrites the sized background.
 ;; The alternative repeats the background instead of stretching it.
 (lambda (g)
  (let ()
   (define background-mode 'stretch)
   (define side (/ (rows g) 2))
   (define out-h (for*/sum ([r (range side)] [c (range side)]) (if (= (at g r c) 0) 0 1)))
   (define out-w (for*/sum ([r (range side)] [c (range side (* 2 side))]) (if (= (at g r c) 0) 0 1)))
   (define background
    (for/list ([r (range out-h)])
     (for/list ([c (range out-w)])
      (let ([sr (if (eq? background-mode 'stretch) (/ (* r side) out-h) (modulo r side))]
            [sc (if (eq? background-mode 'stretch) (/ (* c side) out-w) (modulo c side))])
       (at g (+ side sr) sc)))))
   (for/list ([r (range out-h)])
    (for/list ([c (range out-w)])
     (let ([foreground (at g (+ side (modulo r side)) (+ side (modulo c side)))])
      (if (= foreground 0) (at background r c) foreground)))))))
