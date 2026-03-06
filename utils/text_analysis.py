import re


def word_count(text: str) -> int:
    if not text:
        return 0
    return len(text.split())


def keyword_density(text: str, keyword: str) -> float:
    if not text or not keyword:
        return 0.0
    text_lower = text.lower()
    keyword_lower = keyword.lower()
    total_words = len(text_lower.split())
    if total_words == 0:
        return 0.0
    keyword_words = len(keyword_lower.split())
    count = 0
    words = text_lower.split()
    for i in range(len(words) - keyword_words + 1):
        phrase = " ".join(words[i:i + keyword_words])
        if phrase == keyword_lower:
            count += 1
    return (count * keyword_words / total_words) * 100


def keyword_in_text(text: str, keyword: str) -> bool:
    if not text or not keyword:
        return False
    return keyword.lower() in text.lower()


def extract_first_paragraph(text: str, max_words: int = 100) -> str:
    if not text:
        return ""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return ""
    words = paragraphs[0].split()[:max_words]
    return " ".join(words)


def clean_text(html_text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html_text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
