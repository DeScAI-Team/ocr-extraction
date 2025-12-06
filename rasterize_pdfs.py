import sys
from pathlib import Path
from pdf2image import convert_from_path, pdfinfo_from_path
from tqdm import tqdm

def rasterize_pdfs(pdf_dir, output_dir, dpi=175):
    pdf_dir = Path(pdf_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"no PDF files found {pdf_dir}")
        return
    
    for pdf_file in tqdm(pdf_files, desc="rasterizing PDFs"):
        pdf_name = pdf_file.stem
        pdf_output_dir = output_dir / pdf_name
        pdf_output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Get page count without loading images into memory
            info = pdfinfo_from_path(str(pdf_file))
            page_count = info["Pages"]
            
            # Process one page at a time to avoid OOM on large PDFs
            for page_num in range(1, page_count + 1):
                page_filename = pdf_output_dir / f"p{page_num:04d}.png"
                if page_filename.exists():
                    continue  # Skip already processed pages (resume support)
                
                images = convert_from_path(
                    str(pdf_file), dpi=dpi,
                    first_page=page_num, last_page=page_num,
                    thread_count=4
                )
                images[0].save(page_filename, "PNG")
        except Exception as e:
            print(f"error processing {pdf_file}: {e}")
            continue

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: <pdf_dir> <output_dir> [dpi]")
        sys.exit(1)
    
    pdf_dir = sys.argv[1]
    output_dir = sys.argv[2]
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 175
    
    rasterize_pdfs(pdf_dir, output_dir, dpi)

