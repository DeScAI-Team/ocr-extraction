# ocr-extraction phase 2

Orchestrates OCR over base64-encoded page images (`.b64`), groups pages by PDF, and writes one JSON per PDF with all pages in order. Uses `nanonets/Nanonets-OCR2-3B`.

## Prerequisites (Windows)
- Python 3.10+ (add to PATH)
- Git (optional if you clone)
- GPU recommended; CPU will be slow. If using GPU, install a matching PyTorch+CUDA. 
- If `flash-attn` fails on Windows, remove it from `requirements.txt` and reinstall; script still works (slower) without it.

## Install
```bash
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

If you cloned from GitHub: `git clone <repo_url>` then run the above inside the repo folder.

## Usage
```bash
.venv\Scripts\activate
python run.py ^
  --input-dir C:\path\to\b64 ^
  --output-dir C:\path\to\output ^
  --workers 4
```

What happens:
- Finds all `.b64` files under `--input-dir`
- Decodes each base64 page, runs OCR, groups pages by PDF ID (from filename prefix), and saves one JSON per PDF in `--output-dir`

Expected filenames: `<pdfname>_<page>.b64` (e.g., `report_1.b64`, `report_2.b64`). Pages are sorted by filename. Output JSON: `output_dir/<pdfname>.json`.

### Output JSON example
```json
{
  "pdf_id": "report",
  "pages": [
    {
      "page": "1",
      "source_file": "C:/path/to/report_1.b64",
      "ocr_text": "Extracted text from page 1..."
    }
  ]
}
```

## Adjustable settings (CLI flags)
- `--model` (default `nanonets/Nanonets-OCR2-3B`)
- `--workers` (default 4)
- `--torch-dtype` (default `auto`)
- `--device-map` (default `auto`)
- `--attn-implementation` (default `flash_attention_2`)
- `--max-new-tokens` (default 4096)
- `--do-sample` (enable sampling)
- `--temperature` (default 1.0; sampling)
- `--top-p` (default 1.0; sampling)
- `--repetition-penalty` (default 1.0)
- `--prompt-file` path to custom prompt
- `--system-message` (default as set in code)
- `--no-skip-special-tokens`
- `--no-clean-spaces`

Example with custom prompt and more tokens:
```bash
python run.py ^
  --input-dir C:\data\b64 ^
  --output-dir C:\data\out ^
  --workers 8 ^
  --max-new-tokens 15000 ^
  --prompt-file C:\data\my_prompt.txt
```

## Default prompt (summary)
- Natural reading order
- Tables → HTML
- Equations → LaTeX
- Images → `<img></img>` with caption/description
- Watermarks → `<watermark>…</watermark>`
- Page numbers → `<page_number>…</page_number>`
- Checkboxes → `☐` or `☑`

## Tips
- GPU strongly recommended.
- If `flash-attn` is troublesome, remove it from `requirements.txt`; reinstall.
- Keep filenames consistent so grouping by prefix works (`<pdfname>_<page>.b64`).
