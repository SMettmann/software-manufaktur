from html.parser import HTMLParser
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = ["index.html", "styles.css", "app.js", "impressum.html", "datenschutz.html", "_headers"]
REQUIRED_IDS = {"loesungen", "raumwerk", "entwicklung", "warum-wir", "ueber-uns", "kontakt"}
REQUIRED_TEXT = [
    "Softwaremanufaktur Mettmann",
    "Software, die sich",
    "RAUMWERK",
    "s.mettmann@software-manufraktur.de",
]

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.local_refs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            value = attrs.get(key)
            if not value or value.startswith(("#", "mailto:", "tel:", "http://", "https://")):
                continue
            self.local_refs.append(value.split("#", 1)[0].split("?", 1)[0])


def fail(message):
    print(f"ERROR: {message}")
    return False


def main():
    ok = True
    for filename in REQUIRED_FILES:
        if not (ROOT / filename).is_file():
            ok = fail(f"missing required file: {filename}") and ok

    index_path = ROOT / "index.html"
    if not index_path.is_file():
        return 1

    html = index_path.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(html)

    missing_ids = REQUIRED_IDS - parser.ids
    if missing_ids:
        ok = fail(f"missing required sections: {', '.join(sorted(missing_ids))}") and ok

    for text in REQUIRED_TEXT:
        if text not in html:
            ok = fail(f"required homepage text missing: {text}") and ok

    for ref in parser.local_refs:
        if not ref:
            continue
        if not (ROOT / ref).exists():
            ok = fail(f"broken local reference in index.html: {ref}") and ok

    for page_name in ("index.html", "impressum.html", "datenschutz.html"):
        page = (ROOT / page_name).read_text(encoding="utf-8")
        if not re.search(r'<html[^>]+lang="de"', page, re.I):
            ok = fail(f"missing German language declaration: {page_name}") and ok
        if 'name="viewport"' not in page:
            ok = fail(f"missing responsive viewport: {page_name}") and ok

    if ok:
        print("Static site checks passed.")
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
