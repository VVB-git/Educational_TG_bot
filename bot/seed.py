from __future__ import annotations

from pathlib import Path

import yaml

from bot.config import ANSWERS_DIR, SEED_YAML
from bot.db import Database
from bot.text_format import md_to_html


async def seed_if_empty(db: Database, seed_path: Path = SEED_YAML) -> None:
    if await db.has_any_topics():
        return
    if not seed_path.exists():
        return

    raw = yaml.safe_load(seed_path.read_text(encoding="utf-8")) or {}
    topics = raw.get("topics") or []
    for topic_order, topic in enumerate(topics):
        role_id = topic["role_id"]
        topic_title = topic["title"]
        topic_id = await db.create_topic(role_id, topic_title, sort_order=topic_order)
        for q_order, question in enumerate(topic.get("questions") or []):
            file_name = question["file"]
            md_path = ANSWERS_DIR / file_name
            md_text = md_path.read_text(encoding="utf-8")
            await db.create_question(
                topic_id=topic_id,
                title=question["title"],
                answer_html=md_to_html(md_text),
                images=question.get("images") or [],
                sort_order=q_order,
            )
