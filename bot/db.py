from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id TEXT NOT NULL,
    title TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    answer_html TEXT NOT NULL,
    images TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);
"""


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self.path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA foreign_keys = ON")
        await self._db.executescript(SCHEMA)
        await self._db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    @property
    def db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("База не подключена")
        return self._db

    async def has_any_topics(self) -> bool:
        async with self.db.execute("SELECT 1 FROM topics LIMIT 1") as cursor:
            row = await cursor.fetchone()
        return row is not None

    async def list_topics(self, role_id: str) -> list[dict[str, Any]]:
        sql = """
            SELECT id, role_id, title, sort_order
            FROM topics
            WHERE role_id = ?
            ORDER BY sort_order, id
        """
        async with self.db.execute(sql, (role_id,)) as cursor:
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_topic(self, topic_id: int) -> dict[str, Any] | None:
        sql = "SELECT id, role_id, title, sort_order FROM topics WHERE id = ?"
        async with self.db.execute(sql, (topic_id,)) as cursor:
            row = await cursor.fetchone()
        return dict(row) if row else None

    async def list_questions(self, topic_id: int) -> list[dict[str, Any]]:
        sql = """
            SELECT id, topic_id, title, answer_html, images, sort_order
            FROM questions
            WHERE topic_id = ?
            ORDER BY sort_order, id
        """
        async with self.db.execute(sql, (topic_id,)) as cursor:
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_question(self, question_id: int) -> dict[str, Any] | None:
        sql = """
            SELECT q.id, q.topic_id, q.title, q.answer_html, q.images, q.sort_order,
                   t.role_id, t.title AS topic_title
            FROM questions q
            JOIN topics t ON t.id = q.topic_id
            WHERE q.id = ?
        """
        async with self.db.execute(sql, (question_id,)) as cursor:
            row = await cursor.fetchone()
        return dict(row) if row else None

    async def next_topic_sort(self, role_id: str) -> int:
        sql = "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM topics WHERE role_id = ?"
        async with self.db.execute(sql, (role_id,)) as cursor:
            row = await cursor.fetchone()
        return int(row[0])

    async def next_question_sort(self, topic_id: int) -> int:
        sql = "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM questions WHERE topic_id = ?"
        async with self.db.execute(sql, (topic_id,)) as cursor:
            row = await cursor.fetchone()
        return int(row[0])

    async def create_topic(self, role_id: str, title: str, sort_order: int | None = None) -> int:
        if sort_order is None:
            sort_order = await self.next_topic_sort(role_id)
        cursor = await self.db.execute(
            "INSERT INTO topics (role_id, title, sort_order) VALUES (?, ?, ?)",
            (role_id, title, sort_order),
        )
        await self.db.commit()
        return int(cursor.lastrowid)

    async def create_question(
        self,
        topic_id: int,
        title: str,
        answer_html: str,
        images: list[str] | None = None,
        sort_order: int | None = None,
    ) -> int:
        if sort_order is None:
            sort_order = await self.next_question_sort(topic_id)
        images_json = json.dumps(images or [], ensure_ascii=False)
        cursor = await self.db.execute(
            """
            INSERT INTO questions (topic_id, title, answer_html, images, sort_order)
            VALUES (?, ?, ?, ?, ?)
            """,
            (topic_id, title, answer_html, images_json, sort_order),
        )
        await self.db.commit()
        return int(cursor.lastrowid)
