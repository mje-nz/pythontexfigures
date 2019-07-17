.PHONY: pdf continuous clean extraclean

pdf:
	latexmk -interaction=nonstopmode example.tex

continuous:
	latexmk -pvc example.tex

clean:
	latexmk -c

extraclean: clean
	-rm -rf figures/
