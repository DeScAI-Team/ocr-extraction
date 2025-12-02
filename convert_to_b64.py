import base64
import sys
from pathlib import Path
from tqdm import tqdm

def convert_to_b64(image_dir, output_dir):
    image_dir = Path(image_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_dirs = [d for d in image_dir.iterdir() if d.is_dir()]
    if not pdf_dirs:
        print(f"No PDF directories found in {image_dir}")
        return
    
    for pdf_dir in tqdm(pdf_dirs, desc="Converting to base64"):
        pdf_name = pdf_dir.name
        b64_output_dir = output_dir / pdf_name
        b64_output_dir.mkdir(parents=True, exist_ok=True)
        
        png_files = sorted(pdf_dir.glob("*.png"))
        for png_file in png_files:
            try:
                with open(png_file, "rb") as f:
                    image_data = f.read()
                    b64_data = base64.b64encode(image_data).decode("utf-8")
                
                page_num = png_file.stem
                b64_filename = b64_output_dir / f"{page_num}.b64"
                with open(b64_filename, "w") as f:
                    f.write(b64_data)
                
                png_file.unlink()
            except Exception as e:
                print(f"Error processing {png_file}: {e}")
                continue

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_to_b64.py <image_dir> <output_dir>")
        sys.exit(1)
    
    image_dir = sys.argv[1]
    output_dir = sys.argv[2]
    convert_to_b64(image_dir, output_dir)

