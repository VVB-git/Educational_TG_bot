from __future__ import annotations

import html
import re

TELEGRAM_LIMIT = 4000

_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_URL_RE = re.compile(r"(https?://[^\s<]+)")


def escape_html(text: str) -> str:
    return html.escape(text, quote=False)


def md_to_html(text: str) -> str:
    """Простой Markdown → HTML для Telegram: ссылки, жирный, списки."""
    text = text.replace("\r\n", "\n").strip()
    placeholders: list[str] = []

    def _hold(html_chunk: str) -> str:
        token = f"\x00{len(placeholders)}\x00"
        placeholders.append(html_chunk)
        return token

    def replace_link(match: re.Match[str]) -> str:
        label = html.escape(match.group(1))
        url = html.escape(match.group(2), quote=True)
        return _hold(f'<a href="{url}">{label}</a>')

    def replace_bold(match: re.Match[str]) -> str:
        return _hold(f"<b>{html.escape(match.group(1))}</b>")

    text = _LINK_RE.sub(replace_link, text)
    text = _BOLD_RE.sub(replace_bold, text)

    lines = text.split("\n")
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^[-•]\s+", stripped):
            body = re.sub(r"^[-•]\s+", "", stripped)
            out.append(f"• {html.escape(body)}")
        elif re.match(r"^\d+[.)]\s+", stripped):
            body = re.sub(r"^\d+[.)]\s+", "", stripped)
            num = re.match(r"^(\d+)", stripped).group(1)  # type: ignore[union-attr]
            out.append(f"{num}. {html.escape(body)}")
        else:
            out.append(html.escape(line))
    joined = "\n".join(out)
    for i, chunk in enumerate(placeholders):
        joined = joined.replace(f"\x00{i}\x00", chunk)
    return joined.strip()


def user_text_to_html(text: str) -> str:
    """Текст, который админ прислал руками: экранируем и делаем ссылки кликабельными."""
    escaped = html.escape(text.strip())
    return _URL_RE.sub(lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', escaped)


def split_html(text: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    text = text.strip()
    if len(text) <= limit:
        return [text] if text else [""]

    chunks: list[str] = []
    rest = text
    while rest:
        if len(rest) <= limit:
            chunks.append(rest)
            break
        window = rest[:limit]
        cut = window.rfind("\n\n")
        if cut < limit // 3:
            cut = window.rfind("\n")
        if cut < limit // 3:
            cut = limit
        chunks.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    return [chunk for chunk in chunks if chunk]
