# AI Usage

## AI tools used
1. Claude (Anthropic) chat – used to design and generate the first version of the project from the assignment text and a reference guide.
2. AI coding assistant in VS Code (Claude Code extension) – used to apply one targeted bug fix (deduplication rule) and run the tests.

## What each tool was used for
- Claude chat: project structure, the common data model, initial code for the scrapers (pagination loop, selectors), cleaning, validation, deduplication, the pipeline and CLI, unit tests, and the README draft. It also helped me set up the virtual environment and run the project on my Mac.
- VS Code assistant: edited processing/deduplication.py, added two tests, and updated README/AI_USAGE after I found a bug in my real run.

## Representative prompts
1. "Build the scraping assignment from this document. Use the reference guide for structure (Requests + BeautifulSoup, pagination via the next link, cleaning, validation, deduplication, summary report)."
2. "Why did the duplicate detector remove 'The Star-Touched Queen'? Check what happened." (after my first full run reported 1 duplicate)
3. To the VS Code assistant: "In processing/deduplication.py, change the book fingerprint to source + normalized title + price. books.toscrape.com has two different books titled 'The Star-Touched Queen' (£46.02 and £32.30) and my title-only rule wrongly merged them. Add two tests, update the README, run python -m pytest, and don't run main.py or change other files."

## Which parts were AI-assisted
Nearly all of the code (scrapers/, processing/, pipeline.py, main.py, tests/) was AI-generated and then reviewed and run by me. I ran the scraper, checked the outputs, found the duplicate-detection bug, and decided how to fix it.

## Important changes after reviewing AI output
- Duplicate rule changed: the first book fingerprint was source + title only. My real run removed one record as a "duplicate", but when I compared product URLs and prices, they were two different books (£46.02 and £32.30). I changed the fingerprint to title + price and added tests. Final result: 1,100 rows, 0 duplicates.
- Quote fingerprint: the 50-character cut is taken after normalising the text, not before.
- Run setup: I ran the full scrape from the macOS Terminal because VS Code interrupted the first long run.

## Incorrect or incomplete AI suggestions found
- clean_tags removed duplicates before lowercasing, so "Love" and "love" both stayed. A unit test caught this and it was fixed.
- The AI initially expected 0 duplicates on the real sites; my real run showed the title-only rule was too aggressive (see above).
- The AI could not access the internet when writing the code, so it could not test against the live sites. I did that myself.

## How the final solution was tested and verified
- python -m pytest: 29 unit tests pass (cleaning, validation, deduplication, scraper pagination and failure handling against a fake site, and an end-to-end pipeline test).
- Full run of python main.py: 1,000 books (50 pages) and 100 quotes (10 pages) collected, 1,100 cleaned, 0 rejected, 0 duplicates, 1,100 final rows. counts_reconcile is true. Duration 1,176.5 seconds. The log has no ERROR lines.
- Both "The Star-Touched Queen" books appear in the CSV (2 rows).
- I manually checked rows in final_dataset.csv against the websites: books (price, rating, category) and quotes (author, tags, no quote marks around the text). Book rows have empty author/tags and quote rows have empty price/rating, as designed.
- I ran the project from a virtual environment created from requirements.txt.
