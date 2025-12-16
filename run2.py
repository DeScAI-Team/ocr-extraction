import json
import base64
from pathlib import Path
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from PIL import Image
import io
from transformers import AutoTokenizer, AutoProcessor, AutoModelForImageTextToText
import torch

class OCRProcessor:
    def __init__(
        self,
        model_path: str = "nanonets/Nanonets-OCR2-3B",
        max_workers: int = 4,
        torch_dtype: str = "auto",
        device_map: str = "auto",
        attn_implementation: str = "flash_attention_2",
        max_new_tokens: int = 4096,
        do_sample: bool = False,
        temperature: float = 1.0,
        top_p: float = 1.0,
        repetition_penalty: float = 1.0,
        prompt: str = None,
        system_message: str = ".......",
        skip_special_tokens: bool = True,
        clean_up_tokenization_spaces: bool = True
    ):
        self.model_path = model_path
        self.max_workers = max_workers
        self.torch_dtype = torch_dtype
        self.device_map = device_map
        self.attn_implementation = attn_implementation
        self.max_new_tokens = max_new_tokens
        self.do_sample = do_sample
        self.temperature = temperature
        self.top_p = top_p
        self.repetition_penalty = repetition_penalty
        self.system_message = system_message
        self.skip_special_tokens = skip_special_tokens
        self.clean_up_tokenization_spaces = clean_up_tokenization_spaces
        
        if prompt is None:
            self.prompt = """Extract the text from the above document as if you were reading it naturally. Return the tables in html format. Return the equations in LaTeX representation. If there is an image in the document and image caption is not present, add a small description of the image inside the <img></img> tag; otherwise, add the image caption inside <img></img>. Watermarks should be wrapped in brackets. Ex: <watermark>OFFICIAL COPY</watermark>. Page numbers should be wrapped in brackets. Ex: <page_number>14</page_number> or <page_number>9/22</page_number>. Prefer using ☐ and ☑ for check boxes."""
        else:
            self.prompt = prompt
        
        self.model = None
        self.tokenizer = None
        self.processor = None
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    def _load_model(self):
        if self.model is None:
            model_kwargs = {
                "torch_dtype": self.torch_dtype,
                "device_map": self.device_map
            }
            if self.attn_implementation:
                model_kwargs["attn_implementation"] = self.attn_implementation
            
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_path,
                **model_kwargs
            )
            self.model.eval()
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.processor = AutoProcessor.from_pretrained(self.model_path)
    
    def process_image(self, image_data: bytes) -> str:
        self._load_model()
        
        image = Image.open(io.BytesIO(image_data))
        
        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": [
                {"type": "image", "image": "<image>"},
                {"type": "text", "text": self.prompt},
            ]},
        ]
        
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=[image], padding=True, return_tensors="pt")
        inputs = inputs.to(self.model.device)
        
        generation_kwargs = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": self.do_sample
        }
        
        if self.do_sample:
            generation_kwargs["temperature"] = self.temperature
            generation_kwargs["top_p"] = self.top_p
        
        if self.repetition_penalty != 1.0:
            generation_kwargs["repetition_penalty"] = self.repetition_penalty
        
        with torch.no_grad():
            output_ids = self.model.generate(**inputs, **generation_kwargs)
            generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, output_ids)]
            output_text = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=self.skip_special_tokens,
                clean_up_tokenization_spaces=self.clean_up_tokenization_spaces
            )
        
        return output_text[0]
    
    def process_b64_file(self, b64_path: str) -> Tuple[str, str]:
        with open(b64_path, 'r') as f:
            b64_content = f.read().strip()
        
        image_data = base64.b64decode(b64_content)
        ocr_result = self.process_image(image_data)
        
        return b64_path, ocr_result
    
    def shutdown(self):
        self.executor.shutdown(wait=True)

class Orchestrator:
    def __init__(self, input_dir: str, output_dir: str, ocr_processor: OCRProcessor):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.ocr_processor = ocr_processor
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _group_files_by_pdf(self, b64_files: List[str]) -> Dict[str, List[str]]:
        pdf_groups = defaultdict(list)
        
        for b64_file in b64_files:
            file_path = Path(b64_file)
            file_stem = file_path.stem
            
            pdf_id = file_stem.rsplit('_', 1)[0] if '_' in file_stem else file_stem
            
            pdf_groups[pdf_id].append(b64_file)
        
        for pdf_id in pdf_groups:
            pdf_groups[pdf_id].sort()
        
        return dict(pdf_groups)
    
    def _find_b64_files(self) -> List[str]:
        b64_files = []
        for ext in ['*.b64', '*.B64']:
            b64_files.extend(self.input_dir.rglob(ext))
        return [str(f) for f in b64_files]
    
    def _save_pdf_result(self, pdf_id: str, pages: List[Tuple[str, str]]):
        output_data = {
            "pdf_id": pdf_id,
            "pages": []
        }
        
        for b64_path, ocr_text in sorted(pages, key=lambda x: x[0]):
            page_num = Path(b64_path).stem.split('_')[-1] if '_' in Path(b64_path).stem else "1"
            output_data["pages"].append({
                "page": page_num,
                "source_file": b64_path,
                "ocr_text": ocr_text
            })
        
        output_file = self.output_dir / f"{pdf_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    def process(self):
        b64_files = self._find_b64_files()
        
        if not b64_files:
            print(f"No .b64 files found in {self.input_dir}")
            return
        
        pdf_groups = self._group_files_by_pdf(b64_files)
        
        print(f"Found {len(b64_files)} files across {len(pdf_groups)} PDFs")
        
        futures = []
        for b64_file in b64_files:
            future = self.ocr_processor.executor.submit(
                self.ocr_processor.process_b64_file,
                b64_file
            )
            futures.append((b64_file, future))
        
        results = {}
        completed = 0
        total = len(futures)
        
        for b64_file, future in futures:
            try:
                file_path, ocr_text = future.result()
                results[b64_file] = ocr_text
                completed += 1
                if completed % 10 == 0:
                    print(f"Processed {completed}/{total} files")
            except Exception as e:
                print(f"Error processing {b64_file}: {e}")
                results[b64_file] = None
        
        pdf_results = defaultdict(list)
        for b64_file, ocr_text in results.items():
            if ocr_text is not None:
                file_path = Path(b64_file)
                file_stem = file_path.stem
                pdf_id = file_stem.rsplit('_', 1)[0] if '_' in file_stem else file_stem
                pdf_results[pdf_id].append((b64_file, ocr_text))
        
        for pdf_id, pages in pdf_results.items():
            self._save_pdf_result(pdf_id, pages)
            print(f"Saved results for PDF: {pdf_id} ({len(pages)} pages)")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OCR Processing Orchestrator")
    parser.add_argument("--input-dir", type=str, required=True, help="Directory containing .b64 files")
    parser.add_argument("--output-dir", type=str, required=True, help="Directory to save JSON results")
    parser.add_argument("--model", type=str, default="nanonets/Nanonets-OCR2-3B", help="OCR model path")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker threads")
    parser.add_argument("--torch-dtype", type=str, default="auto", help="Torch dtype for model")
    parser.add_argument("--device-map", type=str, default="auto", help="Device map for model")
    parser.add_argument("--attn-implementation", type=str, default="flash_attention_2", help="Attention implementation")
    parser.add_argument("--max-new-tokens", type=int, default=4096, help="Maximum new tokens for generation")
    parser.add_argument("--do-sample", action="store_true", help="Enable sampling for generation")
    parser.add_argument("--temperature", type=float, default=1.0, help="Temperature for sampling")
    parser.add_argument("--top-p", type=float, default=1.0, help="Top-p for sampling")
    parser.add_argument("--repetition-penalty", type=float, default=1.0, help="Repetition penalty")
    parser.add_argument("--prompt-file", type=str, default=None, help="Path to custom prompt file")
    parser.add_argument("--system-message", type=str, default="You are a helpful assistant.", help="System message")
    parser.add_argument("--no-skip-special-tokens", action="store_true", help="Don't skip special tokens")
    parser.add_argument("--no-clean-spaces", action="store_true", help="Don't clean tokenization spaces")
    
    args = parser.parse_args()
    
    prompt = None
    if args.prompt_file:
        with open(args.prompt_file, 'r') as f:
            prompt = f.read()
    
    ocr_processor = OCRProcessor(
        model_path=args.model,
        max_workers=args.workers,
        torch_dtype=args.torch_dtype,
        device_map=args.device_map,
        attn_implementation=args.attn_implementation,
        max_new_tokens=args.max_new_tokens,
        do_sample=args.do_sample,
        temperature=args.temperature,
        top_p=args.top_p,
        repetition_penalty=args.repetition_penalty,
        prompt=prompt,
        system_message=args.system_message,
        skip_special_tokens=not args.no_skip_special_tokens,
        clean_up_tokenization_spaces=not args.no_clean_spaces
    )
    
    orchestrator = Orchestrator(args.input_dir, args.output_dir, ocr_processor)
    
    try:
        orchestrator.process()
    finally:
        ocr_processor.shutdown()

if __name__ == "__main__":
    main()
