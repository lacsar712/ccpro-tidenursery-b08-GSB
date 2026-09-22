"""幂等轻量迁移：为已有的 feed_events 表补充冲销凭证字段。

新建库由 Base.metadata.create_all 直接建出完整结构；
已存在的旧库则通过 ALTER TABLE 补齐列与约束。生产环境应使用 Alembic，
此处为种子项目的无依赖迁移方案。
"""

from sqlalchemy import text

from app.database import engine


def _column_exists(conn, table: str, column: str) -> bool:
    row = conn.execute(
        text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).first()
    return row is not None


def migrate() -> None:
    with engine.begin() as conn:
        alters = [
            "ALTER TABLE feed_events ADD COLUMN reversal_of_id INTEGER "
            "REFERENCES feed_events(id)",
            "ALTER TABLE feed_events ADD COLUMN reversal_reason VARCHAR(200)",
            "ALTER TABLE feed_events ADD COLUMN reversed_at TIMESTAMP WITH TIME ZONE",
            "ALTER TABLE feed_events ADD COLUMN reversed_by VARCHAR(64)",
        ]
        for column, sql in (
            ("reversal_of_id", alters[0]),
            ("reversal_reason", alters[1]),
            ("reversed_at", alters[2]),
            ("reversed_by", alters[3]),
        ):
            if not _column_exists(conn, "feed_events", column):
                conn.execute(text(sql))
                print(f"migrate: added feed_events.{column}")

        # 同一原投喂只许冲销一次：保证 reversal_of_id 上存在唯一约束。
        # 新建库由 create_all 按默认名创建；旧库或命名不一致时补建具名约束。
        conn.execute(
            text(
                "DO $$ BEGIN "
                "IF NOT EXISTS ("
                "  SELECT 1 FROM pg_constraint c "
                "  JOIN pg_attribute a "
                "    ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey) "
                "  WHERE c.conrelid = 'feed_events'::regclass "
                "    AND c.contype = 'u' AND a.attname = 'reversal_of_id'"
                ") THEN ALTER TABLE feed_events ADD CONSTRAINT uq_feed_events_reversal_of "
                "UNIQUE (reversal_of_id); END IF; END $$"
            )
        )
        # 列表 validOnly / 反查使用的普通索引
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_feed_events_reversal_of_id "
                "ON feed_events (reversal_of_id)"
            )
        )


if __name__ == "__main__":
    migrate()
