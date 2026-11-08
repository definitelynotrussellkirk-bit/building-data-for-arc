# Post-repair solve notes

- **Earlier rule exposure:** yes. I had inspected the task authority while repairing the generator before this episode.
- **Reference consulted during this solve:** no. After preparation I used only `solve/challenge.json`; I did not inspect the generator, Racket source, private labels, or previous solve explanation while implementing this episode.
- **Hypothesis from visible examples:** monochrome hollow rectangles are frames. Every complete non-background object strictly enclosed by a frame changes to that frame's color. Frame cells, background, and objects outside all frames stay unchanged.
- **Evidence in the demonstrations:** role colors vary across examples; one outside color-5 object is preserved; a connected multi-cell color-2 object changes as a whole; and two differently colored objects inside one frame both change.
- **Implementation:** enumerate monochrome 4-connected components, recognize components equal to an exact rectangular perimeter, then recolor any other component whose cells all lie strictly inside that perimeter.
