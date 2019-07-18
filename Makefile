.PHONY: pdf continuous clean

pdf:
	latexmk -interaction=nonstopmode example.tex

continuous:
	latexmk -pvc example.tex

clean:
	latexmk -c
