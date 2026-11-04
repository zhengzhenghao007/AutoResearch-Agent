"""Short-lived parser process. Parent enforces a 45-second deadline."""
import json
import sys
from io import BytesIO


def main():
    from services.parser_limits import apply_parser_limits
    apply_parser_limits()
    from pypdf import PdfReader
    data = sys.stdin.buffer.read(20 * 1024 * 1024 + 1)
    if len(data) > 20 * 1024 * 1024:
        return 1
    reader = PdfReader(BytesIO(data))
    if reader.is_encrypted:
        return 1
    pages, characters, ocr_candidates = [], 0, []
    total = len(reader.pages)
    for i in range(min(total, int(sys.argv[1]))):
        text = reader.pages[i].extract_text() or ''
        # Blank pages must not make otherwise readable PDFs depend on OCR.
        if not text.strip() and has_visual_content(reader.pages[i]):
            ocr_candidates.append(i + 1)
        characters += len(text)
        if characters > 1_000_000:
            return 1
        pages.append({'number': i + 1, 'text': text})
    sys.stdout.buffer.write(json.dumps({'total_pages': total, 'pages': pages, 'ocr_candidates': ocr_candidates}).encode('utf-8'))
    return 0


def has_visual_content(page):
    # Outlined glyphs, inline images and Form XObjects can all have no text
    # layer. Check painting operators, not only image resources. Empty text
    # blocks and genuinely blank pages do not trigger expensive OCR.
    content = page.get_contents()
    painting = {b'Do', b'INLINE IMAGE', b'sh', b'S', b's', b'f', b'F', b'f*', b'B', b'B*', b'b', b'b*'}
    return content is not None and any(operator in painting for _, operator in content.operations)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit(1)
