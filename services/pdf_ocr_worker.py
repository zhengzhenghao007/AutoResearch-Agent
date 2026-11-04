"""Isolated OCR process with bundled models, bounded pixels, pages and output."""
import json
import sys


def main():
    if sys.platform.startswith('linux'):
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
        resource.setrlimit(resource.RLIMIT_CPU, (540, 541))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    import pypdfium2 as pdfium
    from rapidocr_onnxruntime import RapidOCR
    numbers = [int(n) for n in sys.argv[1].split(',')]
    if not numbers or len(numbers) > 20 or len(set(numbers)) != len(numbers):
        return 1
    data = sys.stdin.buffer.read(20 * 1024 * 1024 + 1)
    if len(data) > 20 * 1024 * 1024:
        return 1
    engine = RapidOCR(intra_op_num_threads=1, inter_op_num_threads=1)
    output = {}
    document = pdfium.PdfDocument(data)
    try:
        for number in numbers:
            if not 1 <= number <= len(document):
                return 1
            page = document[number - 1]
            try:
                width, height = page.get_size()
                if width <= 0 or height <= 0:
                    return 1
                scale = min(2.0, 2000 / max(width, height))
                bitmap = page.render(scale=scale)
                try:
                    image = bitmap.to_pil().convert('RGB')
                    try:
                        result, _ = engine(image)
                    finally:
                        image.close()
                finally:
                    bitmap.close()
                # Keep detected line order; no generative correction or invented text.
                output[str(number)] = '\n'.join(line[1] for line in result or [] if line[2] >= 0.5)
                if sum(map(len, output.values())) > 1_000_000:
                    return 1
            finally:
                page.close()
    finally:
        document.close()
    sys.stdout.buffer.write(json.dumps(output, ensure_ascii=False).encode('utf-8'))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit(1)
