from __future__ import annotations
import os
from typing import Optional
from uuid import UUID
import mysql.connector

from models import EnglishTerm, Meaning, SpanishTerm, Example, PartOfSpeech, Gender
from .repository import Repository

class MysqlRepository(Repository):
    def __init__(self):
        self.host = os.getenv("DB_HOST", "127.0.0.1")
        self.user = os.getenv("DB_USER", "root")
        self.pw   = os.getenv("DB_PASSWORD", "example")
        self.db   = os.getenv("DB_NAME", "medical")

    def _connect(self, with_db: bool = True):
        kwargs = dict(host=self.host, user=self.user, password=self.pw)
        if with_db:
            kwargs["database"] = self.db
        return mysql.connector.connect(**kwargs)

    def bootstrap_if_needed(self) -> None:
        cn = self._connect(with_db=False); cur = cn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS medical CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.close(); cn.close()

        cn = self._connect(); cur = cn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS english_term(
            id CHAR(36) PRIMARY KEY,
            lemma VARCHAR(100) NOT NULL,
            pos VARCHAR(20) NOT NULL,
            CONSTRAINT uq_lemma UNIQUE (lemma)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS meaning(
            id CHAR(36) PRIMARY KEY,
            description TEXT NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS spanish_term(
            id CHAR(36) PRIMARY KEY,
            term VARCHAR(100) NOT NULL,
            gender VARCHAR(10) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS example(
            id CHAR(36) PRIMARY KEY,
            language VARCHAR(2) NOT NULL,
            text TEXT NOT NULL,
            meaning_id CHAR(36) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS meaning_english(
            meaning_id CHAR(36) NOT NULL,
            english_term_id CHAR(36) NOT NULL,
            PRIMARY KEY(meaning_id, english_term_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS meaning_spanish(
            meaning_id CHAR(36) NOT NULL,
            spanish_term_id CHAR(36) NOT NULL,
            PRIMARY KEY(meaning_id, spanish_term_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # seed lesion if not there
        cur.execute("SELECT 1 FROM english_term WHERE lemma=%s", ("lesion",))
        if not cur.fetchone():
            cur.execute("INSERT INTO english_term (id, lemma, pos) VALUES (UUID(), %s, %s)", ("lesion", "noun"))
            cn.commit()
        cur.close(); cn.close()

    # ---------- inserts / links ----------
    def insert_english_term(self, term: EnglishTerm) -> None:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("""INSERT INTO english_term (id, lemma, pos)
                       VALUES (%s, %s, %s)""", (str(term.term_id), term.term, term.pos.value))
        cn.commit(); cur.close(); cn.close()

    def insert_meaning(self, meaning: Meaning) -> None:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("INSERT INTO meaning (id, description) VALUES (%s, %s)", (str(meaning.meaning_id), meaning.description))
        cn.commit(); cur.close(); cn.close()

    def insert_spanish_term(self, term: SpanishTerm) -> None:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("INSERT INTO spanish_term (id, term, gender) VALUES (%s, %s, %s)",
                    (str(term.term_id), term.term, term.gender.value))
        cn.commit(); cur.close(); cn.close()

    def insert_example(self, example: Example) -> None:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("INSERT INTO example (id, language, text, meaning_id) VALUES (%s, %s, %s, %s)",
                    (str(example.example_id), example.language, example.text, str(example.meaning.meaning_id)))
        cn.commit(); cur.close(); cn.close()

    def link_meaning_english(self, meaning_id: UUID, english_term_id: UUID) -> None:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("INSERT IGNORE INTO meaning_english (meaning_id, english_term_id) VALUES (%s, %s)",
                    (str(meaning_id), str(english_term_id)))
        cn.commit(); cur.close(); cn.close()

    def link_meaning_spanish(self, meaning_id: UUID, spanish_term_id: UUID) -> None:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("INSERT IGNORE INTO meaning_spanish (meaning_id, spanish_term_id) VALUES (%s, %s)",
                    (str(meaning_id), str(spanish_term_id)))
        cn.commit(); cur.close(); cn.close()

    # ---------- queries ----------
    def load_english_term(self, lemma: str) -> Optional[EnglishTerm]:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("SELECT id, lemma, pos FROM english_term WHERE lemma=%s", (lemma,))
        row = cur.fetchone()
        if not row:
            cur.close(); cn.close(); return None
        tid, lem, pos = row
        et = EnglishTerm(term=lem, pos=PartOfSpeech(pos)); et.term_id = UUID(tid)

        cur.execute("""SELECT m.id, m.description
                       FROM meaning m JOIN meaning_english me ON me.meaning_id=m.id
                       WHERE me.english_term_id=%s""", (tid,))
        for mid, desc in cur.fetchall():
            m = Meaning(description=desc, english_term=et); m.meaning_id = UUID(mid)
            cur.execute("""SELECT s.id, s.term, s.gender
                           FROM spanish_term s JOIN meaning_spanish ms ON ms.spanish_term_id=s.id
                           WHERE ms.meaning_id=%s""", (mid,))
            for sid, sterm, sgender in cur.fetchall():
                st = SpanishTerm(term=sterm, gender=Gender(sgender), meaning=m); st.term_id = UUID(sid)
            cur.execute("SELECT id, language, text FROM example WHERE meaning_id=%s", (mid,))
            for exid, lang, text in cur.fetchall():
                ex = Example(language=lang, text=text, meaning=m); ex.example_id = UUID(exid)
            et.add_meaning(m)

        cur.close(); cn.close()
        return et

    # ---------- NEW: cleanup for tests ----------
    def delete_entry_by_english_lemma(self, lemma: str) -> None:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("SELECT id FROM english_term WHERE lemma=%s", (lemma,))
        row = cur.fetchone()
        if not row:
            cur.close(); cn.close(); return
        (tid,) = row

        # find meaning ids
        cur.execute("SELECT meaning_id FROM meaning_english WHERE english_term_id=%s", (tid,))
        mids = [mid for (mid,) in cur.fetchall()]

        for mid in mids:
            # delete examples
            cur.execute("DELETE FROM example WHERE meaning_id=%s", (mid,))
            # find spanish ids, delete links then spanish terms
            cur.execute("SELECT spanish_term_id FROM meaning_spanish WHERE meaning_id=%s", (mid,))
            sids = [sid for (sid,) in cur.fetchall()]
            cur.execute("DELETE FROM meaning_spanish WHERE meaning_id=%s", (mid,))
            for sid in sids:
                cur.execute("DELETE FROM spanish_term WHERE id=%s", (sid,))
            # delete meaning links + meaning
            cur.execute("DELETE FROM meaning_english WHERE meaning_id=%s", (mid,))
            cur.execute("DELETE FROM meaning WHERE id=%s", (mid,))

        # finally delete the english term
        cur.execute("DELETE FROM english_term WHERE id=%s", (tid,))
        cn.commit(); cur.close(); cn.close()
