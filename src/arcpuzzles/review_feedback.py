"""Read stable feedback IDs without discarding their supporting paragraphs."""
import re


def feedback_items(text: str, *, qualified_headings: bool = True) -> list[dict]:
    # The legacy form is used only to validate summaries made by older builders.
    pattern = r"\s*(?:#{1,6}\s+)?(?:[-*]\s+)?(?:\*\*)?(?P<id>F\d+)(?:\*\*)?"
    if qualified_headings:
        pattern += r"(?P<qualifier>\s+\([^\n)]*\))?(?:\*\*)?"
    heading = re.compile(pattern + r"\s*[:.\u2014\u2013-]\s*(?P<title>.+)")
    items, body = [], []
    for line in text.splitlines():
        match = heading.match(line)
        if match:
            if items:
                items[-1]["text"] = "\n".join(body).strip()
            items.append({"id": match.group("id")})
            qualifier = (match.groupdict().get("qualifier") or "").strip()
            title = match.group("title").rstrip().rstrip("*").rstrip()
            body = [" ".join(part for part in (qualifier, title) if part)]
        elif items:
            body.append(line)
    if items:
        items[-1]["text"] = "\n".join(body).strip()
    return items
