from __future__ import annotations

import hashlib
import os
import tempfile
import threading
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


ROOT_DIR = Path(__file__).resolve().parents[1]
_LOCK = threading.RLock()
_INITIALIZED = False


class StorageError(RuntimeError):
    """Raised when the durable storage backend cannot be synchronized safely."""


@dataclass(frozen=True)
class StorageStatus:
    backend: str
    persistent: bool
    detail: str

    def as_dict(self) -> dict[str, str | bool]:
        return asdict(self)


def _database_url() -> str:
    return (
        os.environ.get("CSE_DATABASE_URL", "").strip()
        or os.environ.get("DATABASE_URL", "").strip()
    )


def _relative_path(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(ROOT_DIR.resolve())
    except ValueError as exc:
        raise StorageError(f"O arquivo {path} está fora do diretório do projeto.") from exc
    return relative.as_posix()


def _target_path(relative_path: str) -> Path:
    candidate = PurePosixPath(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise StorageError(f"Caminho persistido inválido: {relative_path!r}.")
    target = ROOT_DIR.joinpath(*candidate.parts).resolve()
    try:
        target.relative_to(ROOT_DIR.resolve())
    except ValueError as exc:
        raise StorageError(f"Caminho persistido fora do projeto: {relative_path!r}.") from exc
    return target


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _connect():
    try:
        import psycopg
    except ImportError as exc:
        raise StorageError(
            "A persistência PostgreSQL está configurada, mas a dependência psycopg não foi instalada."
        ) from exc

    try:
        return psycopg.connect(_database_url(), connect_timeout=10)
    except Exception as exc:
        raise StorageError(f"Não foi possível conectar ao armazenamento PostgreSQL: {exc}") from exc


def _create_schema(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cse_app_files (
                path TEXT PRIMARY KEY,
                content BYTEA NOT NULL,
                sha256 TEXT NOT NULL,
                revision BIGINT NOT NULL DEFAULT 1,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cse_app_file_history (
                path TEXT NOT NULL,
                revision BIGINT NOT NULL,
                content BYTEA NOT NULL,
                sha256 TEXT NOT NULL,
                archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (path, revision)
            )
            """
        )


def _atomic_write_bytes(content: bytes, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, dir=path.parent) as handle:
        temp_path = Path(handle.name)
        handle.write(content)
    temp_path.replace(path)


def initialize_storage(seed_paths: Iterable[Path]) -> StorageStatus:
    """Seed PostgreSQL once, then restore its latest file snapshots into the runtime."""
    global _INITIALIZED

    database_url = _database_url()
    if not database_url:
        return StorageStatus(
            backend="local",
            persistent=False,
            detail="Arquivos locais do repositório",
        )

    with _LOCK:
        if _INITIALIZED:
            return StorageStatus(
                backend="postgresql",
                persistent=True,
                detail="PostgreSQL sincronizado",
            )

        try:
            with _connect() as connection:
                _create_schema(connection)
                with connection.cursor() as cursor:
                    for path in dict.fromkeys(Path(item) for item in seed_paths):
                        if not path.exists() or not path.is_file():
                            continue
                        content = path.read_bytes()
                        cursor.execute(
                            """
                            INSERT INTO cse_app_files (path, content, sha256)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (path) DO NOTHING
                            """,
                            (_relative_path(path), content, _digest(content)),
                        )
                    cursor.execute("SELECT path, content FROM cse_app_files ORDER BY path")
                    stored_files = cursor.fetchall()

            for relative_path, content in stored_files:
                _atomic_write_bytes(bytes(content), _target_path(str(relative_path)))
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(f"Falha ao inicializar o armazenamento persistente: {exc}") from exc

        _INITIALIZED = True
        return StorageStatus(
            backend="postgresql",
            persistent=True,
            detail=f"PostgreSQL sincronizado ({len(stored_files)} arquivos)",
        )


def persist_files(paths: Iterable[Path]) -> None:
    """Store a consistent snapshot and archive the previous database revision."""
    if not _database_url():
        return

    snapshots: list[tuple[str, bytes, str]] = []
    for path in dict.fromkeys(Path(item) for item in paths):
        if path.exists() and path.is_file():
            content = path.read_bytes()
            snapshots.append((_relative_path(path), content, _digest(content)))

    if not snapshots:
        return

    with _LOCK:
        try:
            with _connect() as connection:
                _create_schema(connection)
                with connection.cursor() as cursor:
                    for relative_path, content, digest in snapshots:
                        cursor.execute(
                            """
                            SELECT content, sha256, revision
                            FROM cse_app_files
                            WHERE path = %s
                            FOR UPDATE
                            """,
                            (relative_path,),
                        )
                        current = cursor.fetchone()
                        if current is None:
                            cursor.execute(
                                """
                                INSERT INTO cse_app_files (path, content, sha256)
                                VALUES (%s, %s, %s)
                                """,
                                (relative_path, content, digest),
                            )
                            continue

                        previous_content, previous_digest, revision = current
                        if str(previous_digest) == digest:
                            continue
                        cursor.execute(
                            """
                            INSERT INTO cse_app_file_history
                                (path, revision, content, sha256)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (path, revision) DO NOTHING
                            """,
                            (
                                relative_path,
                                int(revision),
                                bytes(previous_content),
                                str(previous_digest),
                            ),
                        )
                        cursor.execute(
                            """
                            UPDATE cse_app_files
                            SET content = %s,
                                sha256 = %s,
                                revision = revision + 1,
                                updated_at = NOW()
                            WHERE path = %s
                            """,
                            (content, digest, relative_path),
                        )
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(f"Falha ao salvar os dados no PostgreSQL: {exc}") from exc


def persist_tree(directory: Path) -> None:
    if not directory.exists():
        return
    persist_files(path for path in directory.rglob("*") if path.is_file())
