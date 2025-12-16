import json
import sys
from pathlib import Path

def build_batches(b64_dir, output_dir, pages_per_batch=100):
    b64_dir = Path(b64_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_dirs = [d for d in b64_dir.iterdir() if d.is_dir()]
    if not pdf_dirs:
        print(f"No PDF directories found in {b64_dir}")
        return
    
    all_pages = []
    for pdf_dir in pdf_dirs:
        pdf_id = pdf_dir.name
        b64_files = sorted(pdf_dir.glob("*.b64"))
        for b64_file in b64_files:
            page_num = int(b64_file.stem.replace("p", ""))
            all_pages.append({
                "pdf_id": pdf_id,
                "page_idx": page_num,
                "path": str(b64_file)
            })
    
    batch_num = 1
    current_batch = []
    current_batch_size = 0
    
    for page in all_pages:
        current_batch.append(page)
        current_batch_size += 1
        
        if current_batch_size >= pages_per_batch:
            batch_file = output_dir / f"batch_{batch_num:04d}.jsonl"
            with open(batch_file, "w") as f:
                for item in current_batch:
                    f.write(json.dumps(item) + "\n")
            batch_num += 1
            current_batch = []
            current_batch_size = 0
    
    if current_batch:
        batch_file = output_dir / f"batch_{batch_num:04d}.jsonl"
        with open(batch_file, "w") as f:
            for item in current_batch:
                f.write(json.dumps(item) + "\n")
    
    print(f"Created {batch_num} batches from {len(all_pages)} pages")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python build_batches.py <b64_dir> <output_dir> [pages_per_batch]")
        sys.exit(1)
    
    b64_dir = sys.argv[1]
    output_dir = sys.argv[2]
    pages_per_batch = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    
    build_batches(b64_dir, output_dir, pages_per_batch)

