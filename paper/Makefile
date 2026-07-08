.PHONY: all generate compile clean cleanall

all: generate compile

generate:
	uv run python ../scripts/generate_paper.py --generate-only

compile:
	uv run python ../scripts/generate_paper.py --compile-only

clean:
	uv run python ../scripts/generate_paper.py --clean
	rm -f generated/*.tex

cleanall: clean
	rm -f *.pdf
	rm -f figures/*.pdf
	rm -f tables/*.tex
