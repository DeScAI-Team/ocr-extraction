import sys
import argparse
from pathlib import Path
from rasterize_pdfs import rasterize_pdfs
from convert_to_b64 import convert_to_b64
from build_batches import build_batches

def main():
    parser = argparse.ArgumentParser(
        description="Phase 1: PDF Preprocessing Pipeline - Convert PDFs to batches"
    )
    parser.add_argument(
        "pdf_dir",
        type=str,
        help="Directory containing PDF files"
    )
    parser.add_argument(
        "--output-base",
        type=str,
        default="/lustre/nvwulf/home/cnunberg/ondemand/data/sys/myjobs/projects/descai/ocr1-out",
        help="Base output directory"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="DPI for PDF rasterization (default: 200)"
    )
    parser.add_argument(
        "--pages-per-batch",
        type=int,
        default=100,
        help="Number of pages per batch file (default: 100)"
    )
    parser.add_argument(
        "--skip-rasterize",
        action="store_true",
        help="Skip rasterization step (if PNGs already exist)"
    )
    parser.add_argument(
        "--skip-b64",
        action="store_true",
        help="Skip Base64 conversion step (if B64 files already exist)"
    )
    parser.add_argument(
        "--skip-batches",
        action="store_true",
        help="Skip batch creation step"
    )
    
    args = parser.parse_args()
    
    pdf_dir = Path(args.pdf_dir)
    if not pdf_dir.exists():
        print(f"Error: PDF directory does not exist: {pdf_dir}")
        sys.exit(1)
    
    images_dir = Path(args.output_base) / "images"
    b64_dir = Path(args.output_base) / "b64"
    batches_dir = Path(args.output_base) / "batches"
    
    print("=" * 60)
    print("Phase 1: PDF Preprocessing Pipeline")
    print("=" * 60)
    
    if not args.skip_rasterize:
        print("\n[Step 1/3] Rasterizing PDFs to PNG images...")
        rasterize_pdfs(str(pdf_dir), str(images_dir), dpi=args.dpi)
        print(f"✓ PNG images saved to: {images_dir}")
    else:
        print("\n[Step 1/3] Skipping rasterization (--skip-rasterize)")
    
    if not args.skip_b64:
        print("\n[Step 2/3] Converting PNG images to Base64...")
        print("(PNG files will be deleted after conversion to save space)")
        convert_to_b64(str(images_dir), str(b64_dir))
        print(f"✓ Base64 files saved to: {b64_dir}")
        
        if images_dir.exists():
            for pdf_dir_path in images_dir.iterdir():
                if pdf_dir_path.is_dir() and not any(pdf_dir_path.iterdir()):
                    pdf_dir_path.rmdir()
            if not any(images_dir.iterdir()):
                print(f"✓ Cleaned up empty images directory")
    else:
        print("\n[Step 2/3] Skipping Base64 conversion (--skip-b64)")
    
    if not args.skip_batches:
        print("\n[Step 3/3] Building batches...")
        build_batches(str(b64_dir), str(batches_dir), pages_per_batch=args.pages_per_batch)
        print(f"✓ Batches saved to: {batches_dir}")
    else:
        print("\n[Step 3/3] Skipping batch creation (--skip-batches)")
    
    print("\n" + "=" * 60)
    print("Phase 1 Complete!")
    print("=" * 60)
    print(f"\nOutput structure:")
    print(f"  - Base64 files: {b64_dir}")
    print(f"  - Batch files: {batches_dir}")

if __name__ == "__main__":
    main()

