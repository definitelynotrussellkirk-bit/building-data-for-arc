(rule! (lambda (g)
         (cellmap g (r c v) (if (!= v 5) 5 0))))