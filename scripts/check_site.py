#!/usr/bin/env python3
"""Проверки статического сайта avirbeta.github.io."""

import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

errors = []
warnings = []


def error(message):
    errors.append(message)


def warn(message):
    warnings.append(message)


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.hrefs = []
        self.images = []
        self.blank_links = []
        self.headings = []
        self.translated = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.append(values["id"])
        if tag == "a" and "href" in values:
            self.hrefs.append(values["href"])
            if values.get("target") == "_blank":
                rel = values.get("rel", "")
                if "noopener" not in rel:
                    self.blank_links.append(values["href"])
        if tag == "img":
            self.images.append(values)
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.headings.append(tag)
        if "data-ru" in values or "data-en" in values:
            self.translated.append(values)


def main():
    if not INDEX.is_file():
        error("index.html не найден")
        return finish()

    html = INDEX.read_text(encoding="utf-8")
    lowered = html.lower()

    if "<!doctype html>" not in lowered:
        error("нет <!DOCTYPE html>")
    if not re.search(r'<html[^>]+lang="ru"', lowered):
        error("у <html> должен быть lang=\"ru\"")

    for pattern, name in [
        (r'<meta[^>]+name="viewport"', "viewport"),
        (r'<meta[^>]+name="description"[^>]+content="[^"]+"', "description"),
        (r'<link[^>]+rel="canonical"[^>]+href="https://avirbeta\.github\.io/"', "canonical"),
        (r'<meta[^>]+property="og:title"', "og:title"),
        (r'<meta[^>]+property="og:description"', "og:description"),
        (r'<meta[^>]+property="og:image"', "og:image"),
        (r'<meta[^>]+name="twitter:card"', "twitter:card"),
    ]:
        if not re.search(pattern, html, re.IGNORECASE):
            error(f"нет мета-тега: {name}")

    json_ld = re.findall(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if not json_ld:
        error("нет JSON-LD")
    for block in json_ld:
        try:
            data = json.loads(block)
        except json.JSONDecodeError as exc:
            error(f"JSON-LD не парсится: {exc}")
            continue
        if data.get("@type") != "Person":
            error("JSON-LD должен описывать Person")

    parser = SiteParser()
    parser.feed(html)

    duplicates = [item for item, count in Counter(parser.ids).items() if count > 1]
    if duplicates:
        error(f"дубли id: {duplicates}")

    ids = set(parser.ids)
    for href in parser.hrefs:
        if href.startswith("#") and len(href) > 1 and href[1:] not in ids:
            error(f"битая якорная ссылка: {href}")

    for image in parser.images:
        if not image.get("alt"):
            error(f"у картинки нет alt: {image.get('src')}")

    if parser.blank_links:
        error(f"target=_blank без rel=noopener: {parser.blank_links}")

    if parser.headings.count("h1") != 1:
        error(f"должен быть ровно один h1, найдено: {parser.headings.count('h1')}")

    for values in parser.translated:
        if "data-ru" in values and "data-en" not in values:
            error(f"data-ru без data-en: {values.get('data-ru')}")
        if "data-en" in values and "data-ru" not in values:
            error(f"data-en без data-ru: {values.get('data-en')}")

    if 'id="emailLink"' not in html:
        error("нет ссылки emailLink")

    for name, minimum in [("ава.webp", 10_000), ("og-image.jpg", 20_000)]:
        path = ROOT / name
        if not path.is_file():
            error(f"нет файла {name}")
        elif path.stat().st_size < minimum:
            error(f"файл {name} слишком маленький")

    for name in ["robots.txt", "sitemap.xml", ".nojekyll"]:
        if not (ROOT / name).is_file():
            error(f"нет файла {name}")

    sitemap = ROOT / "sitemap.xml"
    if sitemap.is_file() and "https://avirbeta.github.io/" not in sitemap.read_text(encoding="utf-8"):
        error("sitemap.xml не содержит адрес сайта")

    styles = re.findall(r"<style[^>]*>(.*?)</style>", html, re.DOTALL)
    for block in styles:
        if block.count("{") != block.count("}"):
            error("в CSS не сбалансированы фигурные скобки")

    scripts = [
        block for block in re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.DOTALL | re.IGNORECASE)
        if block.strip() and '"@context"' not in block
    ]
    if not scripts:
        warn("не найдено inline-скриптов")
    else:
        with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
            handle.write("\n".join(scripts))
            script_path = handle.name
        try:
            result = subprocess.run(
                ["node", "--check", script_path],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                error("ошибка синтаксиса JS: " + (result.stderr.strip() or "unknown"))
        except FileNotFoundError:
            error("node не найден — не могу проверить синтаксис JS")
        finally:
            Path(script_path).unlink(missing_ok=True)

    return finish()


def finish():
    for message in warnings:
        print(f"WARN: {message}")
    for message in errors:
        print(f"FAIL: {message}")
    if errors:
        print(f"\nПроверка не пройдена: {len(errors)} ошибок")
        return 1
    print("OK: сайт прошёл проверки")
    return 0


if __name__ == "__main__":
    sys.exit(main())
