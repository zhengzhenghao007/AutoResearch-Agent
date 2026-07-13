from pathlib import Path

import requests
from pypdf import PdfReader


def download_pdf(
    pdf_url: str,
    output_dir: str = "data/papers",
    filename: str = "paper.pdf",
) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / filename

    response = requests.get(pdf_url, timeout=60)
    response.raise_for_status()

    file_path.write_bytes(response.content)

    return file_path


def extract_text_from_pdf(
    pdf_path: str | Path,
    max_pages: int | None = 5,
) -> str:
    reader = PdfReader(str(pdf_path))

    page_count = len(reader.pages)

    if max_pages is None:
        pages_to_read = page_count
    else:
        pages_to_read = min(page_count, max_pages)

    extracted_pages = []

    for page_number in range(pages_to_read):
        page_text = reader.pages[page_number].extract_text() or ""

        extracted_pages.append(
            f"\n--- Page {page_number + 1} ---\n{page_text.strip()}"
        )

    return "\n".join(extracted_pages).strip()