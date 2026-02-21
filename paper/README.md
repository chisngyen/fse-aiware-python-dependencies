# Paper: SmartResolver (FSE 2026 AIWare Competition)

## Format
- **Max 4 pages** including references  
- ACM `acmsmall` format (single-column)  
- Single-blind (author names visible)

## How to Compile
Upload `main.tex` to [Overleaf](https://www.overleaf.com/) or compile locally:
```bash
pdflatex main.tex
pdflatex main.tex  # run twice for references
```

## Before Submission — Update These Placeholders

Search for `XX` in `main.tex` and replace with actual numbers from the final run:

### Author Info (line ~40)
- `Author Name` → your real name
- `University Name` → your affiliation
- `author@university.edu` → your email

### Abstract (line ~55)
- `XX.X%` overall success rate
- `+XX` percentage-point improvement  
- `XX.X%` on conf=0 subset

### Contribution #5 (line ~94)
- `XX.X%` overall success

### Table 1 — Overall Results (line ~225)
- Overall success rate: `XX.X%`
- Snippets resolved: `X,XXX / 2,891`
- Conf=0 resolved: `XXX (XX.X%)`
- Avg time per snippet: `~XX s`
- LLM calls per snippet: `~X.X`

### Table 2 — Error Type Breakdown (line ~245)
Fill in Resolved count and Rate for each error type:
- SyntaxError (437 total)
- ImportError (398 total)
- NoMatchingDist (266 total)
- BuildWheels (71 total)
- AttributeError (64 total)
- Other (72 total)

### Ablation (line ~265)
- Uncomment the ablation table if you have per-component numbers
- Update LLM calls reduction number

### Conclusion (line ~292)
- `XX.X%` success rate
- `[repository URL]` → your GitHub fork URL

## How to Get the Numbers

After the full run completes:
```powershell
# Count results
cd e:\FSE\fse-aiware-python-dependencies\tools\smart-resolver
docker compose exec smart-resolver python -c "
import csv
with open('/output/results.csv') as f:
    rows = list(csv.DictReader(f))
total = len(rows)
success = sum(1 for r in rows if r['success'] == 'True')
print(f'Total: {total}, Success: {success}, Rate: {success/total*100:.1f}%')
"
```
