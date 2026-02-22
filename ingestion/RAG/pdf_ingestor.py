from pathlib import Path
import argparse
import time
from sentence_transformers import SentenceTransformer
from transformers import logging
from dataclasses import dataclass
import re
import json
from pypdf import PdfReader

# Hardcoded for simplicity since we are using devcontainers
OUTPUT_FOLDER = Path("/workspaces/project_1/ingestion/RAG/output")

@dataclass
class Chunk:
    chunk_id: str
    text: str
    page_start: int
    page_end: int

def pdf_to_text(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)
    texts: list[str] = []
    for page in reader.pages:
        t = page.extract_text() or ""
        t = t.replace("\r\n", "\n").replace("\r", "\n")
        texts.append(t)
    return "\n\n".join(texts)

def split_into_paragraphs(text: str) -> list[str]:
    # split on blank lines
    parts = re.split(r"\n\s*\n+", text)
    return [p.strip() for p in parts if p.strip()]

def chunk_paragraphs(
    paragraphs: list[str],
    doc_id: str,
    target_chars: int = 1200,
    overlap_chars: int = 200,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_len = 0
    idx = 0

    for para in paragraphs:
        p_len = len(para) + 1
        if buf_len + p_len > target_chars and buf:
            text = "\n\n".join(buf).strip()
            chunk_id = f"{doc_id}:{idx}"
            chunks.append(Chunk(chunk_id=chunk_id, text=text, page_start=1, page_end=1))
            idx += 1

            # overlap: keep tail of the previous chunk
            if overlap_chars > 0 and len(text) > overlap_chars:
                tail = text[-overlap_chars:]
                buf = [tail]
                buf_len = len(tail)
            else:
                buf = []
                buf_len = 0

        buf.append(para)
        buf_len += p_len

    if buf:
        text = "\n\n".join(buf).strip()
        chunk_id = f"{doc_id}:{idx}"
        chunks.append(Chunk(chunk_id=chunk_id, text=text, page_start=1, page_end=1))

    return chunks

def chunks_to_jsonl(chunks : list[Chunk], out_file : Path):

    logging.set_verbosity_error()
    model = SentenceTransformer("all-MiniLM-L6-v2")
    vectors = model.encode([c.text for c in chunks], normalize_embeddings=True)

    with out_file.open("w", encoding="utf-8") as f:
        for c, v in zip(chunks, vectors):
            record = {
                "chunk_id": c.chunk_id,
                "text": c.text,
                "embedding" : v.tolist()
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {out_file} with {len(chunks)} chunks")

def main():
    parser = argparse.ArgumentParser(description="Convert PDF to text")
    parser.add_argument("--input_pdf", type=str, required=True, help="Path to input PDF file")
    args = parser.parse_args()

    input_pdf = Path(args.input_pdf)
    output_jsonl = Path(OUTPUT_FOLDER, input_pdf.stem + "_vectorized.jsonl")

    print(f"Starting to transform [{input_pdf.name}] to [{output_jsonl.name}]...")

    # (1) Convert PDF into one large string
    start = time.perf_counter()
    pdf_text : str = pdf_to_text(input_pdf)
    print(f"pdf_to_text(): {time.perf_counter() - start:.3f} sec")

    # (2) Split the text into paragraphs which is returned as a list of strings
    paragraphs : list[str] = split_into_paragraphs(pdf_text)

    # (3) Chunk the paragraphs into RAG sized pieces
    chunks : list[Chunk] = chunk_paragraphs(paragraphs, doc_id=input_pdf.stem)

    # (4) Embed the chunks of text into vectors and serialize all chunks and their embeddings into a jsonl file
    #     for the ingestion client
    start = time.perf_counter()
    chunks_to_jsonl(chunks=chunks, out_file=output_jsonl)
    print(f"chunks_to_jsonl(): {time.perf_counter() - start:.3f} sec")

if __name__ == "__main__":
    main()