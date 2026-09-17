"""Short-lived parser process. Parent enforces a 45-second deadline."""
import json
import sys
from io import BytesIO
from pypdf import PdfReader


def main():
    data = sys.stdin.buffer.read(20 * 1024 * 1024 + 1)
    if len(data) > 20 * 1024 * 1024:
        return 1
    reader = PdfReader(BytesIO(data))
    if reader.is_encrypted:
        return 1
    pages, characters = [], 0
    total = len(reader.pages)
    for i in range(min(total, int(sys.argv[1]))):
        text = reader.pages[i].extract_text() or ''
        characters += len(text)
        if characters > 1_000_000:
            return 1
        pages.append({'number': i + 1, 'text': text})
    sys.stdout.buffer.write(json.dumps({'total_pages': total, 'pages': pages}).encode('utf-8'))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit(1)
