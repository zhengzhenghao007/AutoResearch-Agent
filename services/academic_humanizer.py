"""Publication boundary for generated prose. All edits are local and reversible."""
import logging
import re
from contextvars import ContextVar
from functools import lru_cache
from pathlib import Path

from services.humanizer_policy import profile

logger = logging.getLogger(__name__)
_ACTIVE = ContextVar('academic_humanizer_active', default=False)
MAX_PARAGRAPH_CHARS = 32000
_LEXICON = Path(__file__).resolve().parents[1] / 'vendor/academic_humanizer/references/lexicon.txt'
_BREAK = re.compile(r'(?:\r?\n)[ \t]*(?:\r?\n)')
# State is per document or per stream, never shared by different users.
_FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})(.*)$', re.MULTILINE)
_REFERENCE_SECTION = re.compile(r'^\s*#*\s*(?:references|bibliography|参考文献)\s*[:：]?\s*$', re.I | re.M)


class _LiteralContext:
    def __init__(self):
        self.fence = None
        self.opaque = False
        self.display_math = False
        self.quotation = False
        self.latex_display = False

    def protected(self, text):
        if self.opaque:
            return True
        inside = bool(self.fence or self.display_math or self.quotation or self.latex_display)
        fences = list(_FENCE.finditer(text))
        for match in fences:
            marker, info = match.groups()
            if self.fence is None:
                self.fence = marker
            elif marker.startswith(self.fence) and not info.strip():
                self.fence = None
        if fences or self.fence:
            return True
        if _REFERENCE_SECTION.search(text) or text.lstrip().startswith(('{','[','---','\\documentclass','\\begin')):
            self.opaque = True
            return True
        if r'\begin{' in text or r'\documentclass' in text:
            self.opaque = True
            return True
        if r'\[' in text or r'\]' in text:
            self.latex_display = text.rfind(r'\[') > text.rfind(r'\]')
            return True
        if text.count('$$') % 2:
            self.display_math = not self.display_math
        if text.count('"') % 2 or (text.count('“') + text.count('”')) % 2:
            self.quotation = not self.quotation
        return inside or self.display_math or self.quotation or self.latex_display or text.lstrip().startswith(('>', '“', '"', '‘'))


_EN = re.compile(r'^(?:It is (?:worth noting|important to note)|It should be noted) that (?P<lead>the|we|this|these|our|they|it|there|a|an)\b')
_ZH = re.compile(r'^(?:(?:值得(?:注意|一提|关注|指出)|需要(?:指出|强调|注意|说明))的是)[，,]')


# These conjunctions introduce purpose or condition. Only replace the introductory words.
_CONCISE = {'In order to ': 'To ', 'In the event that ': 'If ',
            'In spite of the fact that ': 'Although ', 'Due to the fact that ': 'Because '}


@lru_cache(maxsize=1)
def _openers():
    from vendor.academic_humanizer.scripts.check_revision import Lexicon
    return tuple(rx for category, rx in Lexicon(_LEXICON).patterns if category in {'emphasis', 'zh_emphasis'})


def _edit(text):
    """Return a prefix replacement only when the upstream cleanup lexicon agrees."""
    for original, revised in _CONCISE.items():
        if text.startswith(original) and text[len(original):].strip() and profile() == 'standard':
            return revised + text[len(original):]
    match = _EN.match(text) or _ZH.match(text)
    if not match or not any(rx.match(text) for rx in _openers()):
        return text
    prefix = match.groupdict().get('lead')
    rest = text[match.end():]
    if not rest.strip():
        return text
    revised = (prefix.capitalize() if prefix else '') + rest
    # Stacked openers could otherwise change again at a later publication boundary.
    return text if _EN.match(revised) or _ZH.match(revised) else revised


def _consistent(original, revised):
    # The entire claim must be byte-for-byte identical after the approved discourse marker.
    match = _EN.match(original) or _ZH.match(original)
    if match:
        expected = (match.groupdict().get('lead') or '').capitalize() + original[match.end():]
    else:
        expected = next((new + original[len(old):] for old, new in _CONCISE.items() if original.startswith(old)), None)
    if revised != expected:
        return False
    from vendor.academic_humanizer.scripts.check_revision import Doc
    before, after = (Doc('output.md', raw=value) for value in (original,revised))
    return all(getattr(before, key) == getattr(after, key) for key in ('cites','refs','math','formal','preamble')) and [n[0] for n in before.numbers] == [n[0] for n in after.numbers]


def _paragraph(text):
    if len(text) > MAX_PARAGRAPH_CHARS or not text.strip() or text.startswith((' ', '\t')):
        return text
    candidate = _edit(text)
    if candidate == text:
        return text
    if not _consistent(text, candidate):
        raise ValueError('consistency check rejected the proposed edit')
    return candidate if _edit(candidate) == candidate else text


def humanize(text: str) -> str:
    """Apply Academic Humanizer to generated text only. Never log its content."""
    if not isinstance(text, str) or not text or _ACTIVE.get():
        return text
    token = _ACTIVE.set(True)
    try:
        context = _LiteralContext()
        pieces = []
        offset = 0
        for boundary in _BREAK.finditer(text):
            paragraph = text[offset:boundary.start()]
            pieces.extend((paragraph if context.protected(paragraph) else _paragraph(paragraph), boundary.group()))
            offset = boundary.end()
        tail = text[offset:]
        return ''.join(pieces) + (tail if context.protected(tail) else _paragraph(tail))
    except Exception as error:
        logger.warning('Academic Humanizer kept original output (%s)', type(error).__name__)
        return text
    finally:
        _ACTIVE.reset(token)


class ParagraphStream:
    """Receive decoded prose deltas; emit only complete, checked paragraphs."""
    def __init__(self):
        self.pending = ''
        self.context = _LiteralContext()
        self.oversized = False

    def feed(self, chunk, *, final=False):
        if self.oversized:
            yield chunk
            return
        self.pending += chunk
        offset = 0
        for boundary in _BREAK.finditer(self.pending):
            paragraph = self.pending[offset:boundary.start()]
            yield (paragraph if self.context.protected(paragraph) else humanize(paragraph)) + boundary.group()
            offset = boundary.end()
        self.pending = self.pending[offset:]
        if len(self.pending) > MAX_PARAGRAPH_CHARS:
            logger.warning('Academic Humanizer stream exceeded paragraph limit; preserving remaining output')
            self.oversized = True
            yield self.pending
            self.pending = ''
        if final and self.pending:
            yield self.pending if self.context.protected(self.pending) else humanize(self.pending)
            self.pending = ''
