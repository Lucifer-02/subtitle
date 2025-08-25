SRT_FILE = "../video_trans/dataset/sub.srt"

run: 
	clear
	# uv run main.py
	# apply
	uv run test.py

run:
	uv run test.py

gen: clean
	uv run main.py gen-prompts --srt-file $(SRT_FILE) --limit 150 --output-dir prompts/

apply:
	uv run main.py apply-translation --srt-file $(SRT_FILE)  --translation-file ./out.txt

clean:
	rm -f ./prompts/* || rm out.txt

# simplify sub: %s/^\d\+\n.*\n\(.*\)\n/\1
