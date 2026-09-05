# ADR-005 — SQLAlchemy 2.x async

**Status:** aceito. API 2.0 (`select()`, `Mapped[T]`, `mapped_column`), `AsyncSession` + asyncpg.
Sem `session.query` legado. Session por unidade de trabalho (nunca global). Loader strategies
explícitos (`selectinload`/`joinedload`) para replicar os `Include` do .NET sem N+1.
