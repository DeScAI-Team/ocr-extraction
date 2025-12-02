
## Phase 1
## Installation

```bash
brew install poppler  # change it for OS you need 
pip install pdf2image Pillow tqdm
```

## Usage

Run the complete pipeline:
```bash
python run.py /path/to/pdfs
```

### Options

```bash
python run.py <pdf_dir> [OPTIONS]

Options:
  --output-base DIR    Output directory (default: data)
  --dpi N             DPI for PDF rasterization (default: 200)
  --pages-per-batch N Pages per batch file (default: 100)
  --skip-rasterize    Skip rasterization step
  --skip-b64          Skip Base64 conversion step
  --skip-batches      Skip batch creation step
```

## Output

```
data/
├── b64/              # Base64 encoded images
│   └── {pdf_name}/
│       └── p{page_num:04d}.b64
└── batches/          # JSONL batch files
    └── batch_{num:04d}.jsonl
```

PNG files are automatically deleted after Base64 conversion to save storage

## Individual Steps

You can also run each step separately:

```bash
python rasterize_pdfs.py <pdf_dir> <output_dir> [dpi]
python convert_to_b64.py <image_dir> <output_dir>
python build_batches.py <b64_dir> <output_dir> [pages_per_batch]
```

## Phase 2 ( to be continued... )
