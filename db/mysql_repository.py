from __future__ import annotations

import os
from typing import Optional, Iterable
from uuid import UUID

import mysql.connector
from mysql.connector import Error, IntegrityError

from .repository import Repository
from models import (
    EnglishTerm,
    Meaning,
    SpanishTerm,
    Example,
    PartOfSpeech,
    Gender,
)

class MysqlRepository(Repository):
    def __init__(
        self,
        host: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        port: Optional[int] = None,
    ) -> None:
        self.host = host or os.getenv("MYSQL_HOST", "127.0.0.1")
        self.user = user or os.getenv("MYSQL_USER", "root")
        self.password = password or os.getenv("MYSQL_PASSWORD", "example")
        self.database = database or os.getenv("MYSQL_DATABASE", "medical")
        self.port = int(port or os.getenv("MYSQL_PORT", "3306"))


    def _connect(self, with_db: bool = True):
        kwargs = dict(
            host=self.host,
            user=self.user,
            password=self.password,
            port=self.port,
            autocommit=False,
        )
        if with_db:
            kwargs["database"] = self.database
        return mysql.connector.connect(**kwargs)

    def bootstrap_if_needed(self) -> None:
        """
        Ensure DB and tables exist. Also insert a tiny seed if 'lesion' is missing.
        Tests call this once per module.
        """
        cn = self._connect(with_db=False)
        cur = cn.cursor()
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{self.database}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cn.commit()
        cur.close()
        cn.close()

        cn = self._connect(with_db=True)
        cur = cn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS english_term (
                id CHAR(36) NOT NULL,
                lemma VARCHAR(255) NOT NULL,
                pos VARCHAR(30) NOT NULL,
                PRIMARY KEY (id),
                UNIQUE KEY uq_lemma (lemma)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS meaning (
                id CHAR(36) NOT NULL,
                description TEXT NOT NULL,
                PRIMARY KEY (id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS spanish_term (
                id CHAR(36) NOT NULL,
                term VARCHAR(255) NOT NULL,
                gender VARCHAR(10) NOT NULL,
                PRIMARY KEY (id),
                UNIQUE KEY uq_spanish_term (term)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS example (
                id CHAR(36) NOT NULL,
                language VARCHAR(5) NOT NULL,
                text TEXT NOT NULL,
                meaning_id CHAR(36) NOT NULL,
                PRIMARY KEY (id),
                KEY idx_example_meaning (meaning_id),
                CONSTRAINT fk_example_meaning
                    FOREIGN KEY (meaning_id) REFERENCES meaning(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS meaning_english (
                meaning_id CHAR(36) NOT NULL,
                english_term_id CHAR(36) NOT NULL,
                PRIMARY KEY (meaning_id, english_term_id),
                KEY idx_me_eng (english_term_id),
                CONSTRAINT fk_me_meaning
                    FOREIGN KEY (meaning_id) REFERENCES meaning(id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_me_english
                    FOREIGN KEY (english_term_id) REFERENCES english_term(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS meaning_spanish (
                meaning_id CHAR(36) NOT NULL,
                spanish_term_id CHAR(36) NOT NULL,
                PRIMARY KEY (meaning_id, spanish_term_id),
                KEY idx_ms_span (spanish_term_id),
                CONSTRAINT fk_ms_meaning
                    FOREIGN KEY (meaning_id) REFERENCES meaning(id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_ms_spanish
                    FOREIGN KEY (spanish_term_id) REFERENCES spanish_term(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        cn.commit()

        cur.execute("SELECT 1 FROM english_term WHERE lemma=%s", ("lesion",))
        exists = cur.fetchone()
        if not exists:
            et = EnglishTerm(term="lesion", pos=PartOfSpeech.NOUN)
            m = Meaning(description="Pathological change; abnormal tissue", english_term=et)
            es = SpanishTerm(term="lesión", gender=Gender.FEMININE, meaning=m)
            ex1 = Example(language="en", text="The MRI showed a brain lesion.", meaning=m)
            ex2 = Example(language="es", text="La resonancia mostró una lesión cerebral.", meaning=m)
            self.persist_entry_graph(et, m, es, [ex1, ex2], _cn=cn)

        cur.close()
        cn.close()

    def load_english_term(self, lemma: str) -> Optional[EnglishTerm]:
        cn = self._connect()
        cur = cn.cursor()

        cur.execute("SELECT id, lemma, pos FROM english_term WHERE lemma=%s", (lemma,))
        row = cur.fetchone()
        if not row:
            cur.close()
            cn.close()
            return None

        et_id, lem, pos = row
        et = EnglishTerm(term=lem, pos=PartOfSpeech(pos))
        # set DB UUID captured from SQL (dataclass field allows assignment)
        et.term_id = UUID(et_id)

        # meanings
        cur.execute(
            """
            SELECT m.id, m.description
            FROM meaning m
            JOIN meaning_english me ON me.meaning_id = m.id
            WHERE me.english_term_id = %s
            """,
            (et_id,),
        )
        meaning_rows = cur.fetchall()
        meanings_by_id = {}

        for mid, desc in meaning_rows:
            meaning = Meaning(description=desc, english_term=et)
            meaning.meaning_id = UUID(mid)
            et.add_meaning(meaning)
            meanings_by_id[mid] = meaning

        if meaning_rows:
            ids = tuple(mid for mid, _ in meaning_rows)
            # Prepare IN clause
            in_clause = ",".join(["%s"] * len(ids))
            cur.execute(
                f"""
                SELECT ms.meaning_id, s.id, s.term, s.gender
                FROM meaning_spanish ms
                JOIN spanish_term s ON s.id = ms.spanish_term_id
                WHERE ms.meaning_id IN ({in_clause})
                """,
                ids,
            )
            for m_id, s_id, s_term, s_gender in cur.fetchall():
                meaning = meanings_by_id[m_id]
                st = SpanishTerm(term=s_term, gender=Gender(s_gender), meaning=meaning)
                st.term_id = UUID(s_id)

        for mid, _ in meaning_rows:
            cur.execute(
                "SELECT id, language, text FROM example WHERE meaning_id=%s",
                (mid,),
            )
            for ex_id, lang, text in cur.fetchall():
                meaning = meanings_by_id[mid]
                ex = Example(language=lang, text=text, meaning=meaning)
                ex.example_id = UUID(ex_id)

        cur.close()
        cn.close()
        return et

    def insert_english_term(self, term: EnglishTerm) -> None:
        cn = self._connect()
        try:
            cur = cn.cursor()
            cur.execute(
                """
                INSERT INTO english_term (id, lemma, pos)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE pos = VALUES(pos)
                """,
                (str(term.term_id), term.term, term.pos.value),
            )
            cn.commit()
        finally:
            cur.close()
            cn.close()

    def insert_meaning(self, meaning: Meaning) -> None:
        cn = self._connect()
        try:
            cur = cn.cursor()
            cur.execute(
                "INSERT INTO meaning (id, description) VALUES (%s, %s)",
                (str(meaning.meaning_id), meaning.description),
            )
            cn.commit()
        finally:
            cur.close()
            cn.close()

    def insert_spanish_term(self, term: SpanishTerm) -> None:
        cn = self._connect()
        try:
            cur = cn.cursor()
            cur.execute(
                """
                INSERT INTO spanish_term (id, term, gender)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE gender = VALUES(gender)
                """,
                (str(term.term_id), term.term, term.gender.value),
            )
            cn.commit()
        finally:
            cur.close()
            cn.close()

    def insert_example(self, example: Example) -> None:
        cn = self._connect()
        try:
            cur = cn.cursor()
            cur.execute(
                """
                INSERT INTO example (id, language, text, meaning_id)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    str(example.example_id),
                    example.language,
                    example.text,
                    str(example.meaning.meaning_id),
                ),
            )
            cn.commit()
        finally:
            cur.close()
            cn.close()

    def link_meaning_english(self, meaning_id: UUID, english_term_id: UUID) -> None:
        cn = self._connect()
        try:
            cur = cn.cursor()
            cur.execute(
                """
                INSERT IGNORE INTO meaning_english (meaning_id, english_term_id)
                VALUES (%s, %s)
                """,
                (str(meaning_id), str(english_term_id)),
            )
            cn.commit()
        finally:
            cur.close()
            cn.close()

    def link_meaning_spanish(self, meaning_id: UUID, spanish_term_id: UUID) -> None:
        cn = self._connect()
        try:
            cur = cn.cursor()
            cur.execute(
                """
                INSERT IGNORE INTO meaning_spanish (meaning_id, spanish_term_id)
                VALUES (%s, %s)
                """,
                (str(meaning_id), str(spanish_term_id)),
            )
            cn.commit()
        finally:
            cur.close()
            cn.close()

    def persist_entry_graph(
        self,
        english: EnglishTerm,
        meaning: Meaning,
        spanish: SpanishTerm,
        examples: Iterable[Example],
        _cn=None,  
    ) -> None:
        """
        High-level, single-transaction persist that the Service calls.
        Idempotent for english/spanish (unique on lemma/term).
        """
        cn = _cn or self._connect()
        created_here = _cn is None
        try:
            cur = cn.cursor()

            cur.execute(
                "SELECT id FROM english_term WHERE lemma=%s",
                (english.term,),
            )
            row = cur.fetchone()
            if row:
                english.term_id = UUID(row[0])
                cur.execute(
                    "UPDATE english_term SET pos=%s WHERE id=%s",
                    (english.pos.value, str(english.term_id)),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO english_term (id, lemma, pos)
                    VALUES (%s, %s, %s)
                    """,
                    (str(english.term_id), english.term, english.pos.value),
                )

            cur.execute(
                "INSERT INTO meaning (id, description) VALUES (%s, %s)",
                (str(meaning.meaning_id), meaning.description),
            )

            cur.execute("SELECT id FROM spanish_term WHERE term=%s", (spanish.term,))
            srow = cur.fetchone()
            if srow:
                spanish.term_id = UUID(srow[0])
                cur.execute(
                    "UPDATE spanish_term SET gender=%s WHERE id=%s",
                    (spanish.gender.value, str(spanish.term_id)),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO spanish_term (id, term, gender)
                    VALUES (%s, %s, %s)
                    """,
                    (str(spanish.term_id), spanish.term, spanish.gender.value),
                )

            cur.execute(
                """
                INSERT IGNORE INTO meaning_english (meaning_id, english_term_id)
                VALUES (%s, %s)
                """,
                (str(meaning.meaning_id), str(english.term_id)),
            )
            cur.execute(
                """
                INSERT IGNORE INTO meaning_spanish (meaning_id, spanish_term_id)
                VALUES (%s, %s)
                """,
                (str(meaning.meaning_id), str(spanish.term_id)),
            )

            for ex in examples:
                cur.execute(
                    """
                    INSERT INTO example (id, language, text, meaning_id)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (str(ex.example_id), ex.language, ex.text, str(meaning.meaning_id)),
                )

            cn.commit()
        except Exception:
            cn.rollback()
            raise
        finally:
            if created_here:
                cur.close()
                cn.close()

    def delete_entry_by_english_lemma(self, lemma: str) -> None:
        """
        Test helper: remove an English entry and its newly created graph.
        We only delete meanings that are solely linked to this English term.
        """
        cn = self._connect()
        try:
            cur = cn.cursor()

            # find english id
            cur.execute("SELECT id FROM english_term WHERE lemma=%s", (lemma,))
            row = cur.fetchone()
            if not row:
                cn.rollback()
                return
            en_id = row[0]

            cur.execute(
                """
                SELECT m.id
                FROM meaning m
                JOIN meaning_english me ON me.meaning_id = m.id
                WHERE me.english_term_id = %s
                """,
                (en_id,),
            )
            meaning_ids = [mid for (mid,) in cur.fetchall()]

            for mid in meaning_ids:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM meaning_english
                    WHERE meaning_id=%s AND english_term_id<>%s
                    """,
                    (mid, en_id),
                )
                (others,) = cur.fetchone()

                if others == 0:
                    # find spanish ids linked to this meaning
                    cur.execute(
                        "SELECT spanish_term_id FROM meaning_spanish WHERE meaning_id=%s",
                        (mid,),
                    )
                    spanish_ids = [sid for (sid,) in cur.fetchall()]

                    cur.execute("DELETE FROM example WHERE meaning_id=%s", (mid,))
                    cur.execute("DELETE FROM meaning_spanish WHERE meaning_id=%s", (mid,))
                    cur.execute(
                        "DELETE FROM meaning_english WHERE meaning_id=%s AND english_term_id=%s",
                        (mid, en_id),
                    )
                    cur.execute("DELETE FROM meaning WHERE id=%s", (mid,))
                    if spanish_ids:
                        in_clause = ",".join(["%s"] * len(spanish_ids))
                        cur.execute(
                            f"""
                            DELETE s FROM spanish_term s
                            LEFT JOIN meaning_spanish ms ON ms.spanish_term_id = s.id
                            WHERE s.id IN ({in_clause})
                            AND ms.spanish_term_id IS NULL
                            """,
                            spanish_ids,
                        )
                else:
                    cur.execute(
                        "DELETE FROM meaning_english WHERE meaning_id=%s AND english_term_id=%s",
                        (mid, en_id),
                    )

            cur.execute("DELETE FROM english_term WHERE id=%s", (en_id,))
            cn.commit()
        except Exception:
            cn.rollback()
            raise
        finally:
            cur.close()
            cn.close()
