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
        if not text.strip() and contains_image(reader.pages[i].get('/Resources')):
            ocr_candidates.append(i + 1)
        characters += len(text)
        if characters > 1_000_000:
            return 1
        pages.append({'number': i + 1, 'text': text})
    sys.stdout.buffer.write(json.dumps({'total_pages': total, 'pages': pages, 'ocr_candidates': ocr_candidates}).encode('utf-8'))
    return 0


def contains_image(resources, depth=0):
    if resources is None or depth > 10:
        return False
    objects = resources.get_object().get('/XObject', {})
    for ref in list(objects.get_object().values() if hasattr(objects, 'get_object') else objects.values())[:1000]:
        obj = ref.get_object()
        if obj.get('/Subtype') == '/Image':
            return True
        if obj.get('/Subtype') == '/Form' and contains_image(obj.get('/Resources'), depth + 1):
            return True
    return False


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit(1)
