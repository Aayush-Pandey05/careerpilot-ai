import re


def source_quote(text: str, quote: str) -> str:
    """Resolve a quote to its original source span, allowing only whitespace changes."""
    words = quote.split()
    if not words:
        return ""
    match = re.search(r"\s+".join(re.escape(word) for word in words), text)
    return match.group() if match else ""
