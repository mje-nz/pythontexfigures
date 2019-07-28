.PHONY: all clean

all:
	cd basic; latexmk example.tex
	cd subfiles; latexmk example-with-subfiles.tex
	cd subfiles; latexmk sections/section1/section1.tex
	cd subfiles; latexmk sections/section2/section2.tex

clean:
	cd basic; latexmk -c example.tex
	cd subfiles; latexmk -c example-with-subfiles.tex
	cd subfiles; latexmk -c sections/section1/section1.tex
	cd subfiles; latexmk -c sections/section2/section2.tex
