SRT_FILE = "/media/lucifer/STORAGE/IMPORTANT/learning/sup/Week_1:_Supply_Chain_Management_-_Core_Concepts/Video 4: Supply Chain Management Perspectives/MITSCXX1T314-V006600_100-en.srt"

run: apply
	# clear
	# uv run main.py
	# apply

gen: clean
	uv run main.py gen-prompts --srt-file $(SRT_FILE) --limit 100 --output-dir prompts/

apply:
	uv run main.py apply-translation --srt-file $(SRT_FILE)  --translation-file ./out.txt

clean:
	rm -f ./prompts/* || rm out.txt
