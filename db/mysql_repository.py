from __future__ import annotations
import os, pathlib
from typing import Optional, List
from uuid import UUID

import mysql.connector
from mysql.connector.connection import MySQLConnection

from models import EnglishTerm, SpanishTerm, Meaning, Example, PartOfSpeech, Gender

def _to_str(u: UUID | str) -> str:
    return str(u)

class MysqlRepository:
    def __init__(self,
                 host: str | None = None,
                 user: str | None = None,
                 password: str | None = None,
                 database: str | None = None):
        self.host = host or os.getenv("MYSQL_HOST", "127.0.0.1")
        self.user = user or os.getenv("MYSQL_USER", "root")
        self.password = password or os.getenv("MYSQL_PASSWORD", "example")
        self.database = database or os.getenv("MYSQL_DATABASE", "medical")
        self.port = int(os.getenv("MYSQL_PORT", "3306"))

    def _connect(self, with_db: bool = True) -> MySQLConnection:
        kwargs = dict(host=self.host, user=self.user, password=self.password, port=self.port)
        if with_db:
            kwargs["database"] = self.database
        return mysql.connector.connect(**kwargs)

    # ---------- bootstrap / maintenance ----------
    def bootstrap_if_needed(self) -> None:
        # create DB if needed
        cn = self._connect(with_db=False); cur = cn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cn.commit(); cur.close(); cn.close()

        # do tables exist?
        cn = self._connect(); cur = cn.cursor()
        cur.execute("""SELECT COUNT(*) FROM information_schema.tables
                       WHERE table_schema=%s AND table_name IN
                       ('english_term','spanish_term','meaning','example','meaning_english','meaning_spanish')""",
                    (self.database,))
        count = cur.fetchone()[0]; cur.close(); cn.close()
        if count >= 6:
            return

        # run init.sql
        sql_path = pathlib.Path("data/init.sql")
        text = sql_path.read_text(encoding="utf-8")
        cn = self._connect(); cur = cn.cursor()
        for stmt in text.split(';'):
            s = stmt.strip()
            if s:
                cur.execute(s)
        cn.commit(); cur.close(); cn.close()

    def clear_all_data(self) -> None:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for t in ("meaning_english","meaning_spanish","example","meaning","english_term","spanish_term"):
            cur.execute(f"TRUNCATE TABLE {t}")
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
        cn.commit(); cur.close(); cn.close()

    # ---------- inserts ----------
    def insert_english_term(self, term: EnglishTerm) -> None:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("""INSERT INTO english_term (id, lemma, pos)
                       VALUES (%s, %s, %s)""", (_to_str(term.term_id), term.term, term.pos.value))
        cn.commit(); cur.close(); cn.close()

    def insert_spanish_term(self, term: SpanishTerm) -> None:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("""INSERT INTO spanish_term (id, term, gender)
                       VALUES (%s, %s, %s)""", (_to_str(term.term_id), term.term, term.gender.value))
        cn.commit(); cur.close(); cn.close()

    def insert_meaning(self, meaning: Meaning) -> None:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("""INSERT INTO meaning (id, description)
                       VALUES (%s, %s)""", (_to_str(meaning.meaning_id), meaning.description))
        cn.commit(); cur.close(); cn.close()

    def insert_example(self, example: Example) -> None:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("""INSERT INTO example (id, meaning_id, language, text)
                       VALUES (%s, %s, %s, %s)""",
                    (_to_str(example.example_id), _to_str(example.meaning.meaning_id), example.language, example.text))
        cn.commit(); cur.close(); cn.close()

    # ---------- link tables ----------
    def link_meaning_english(self, meaning_id: UUID, english_term_id: UUID) -> None:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("""INSERT IGNORE INTO meaning_english (meaning_id, english_term_id)
                       VALUES (%s, %s)""", (_to_str(meaning_id), _to_str(english_term_id)))
        cn.commit(); cur.close(); cn.close()

    def link_meaning_spanish(self, meaning_id: UUID, spanish_term_id: UUID) -> None:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("""INSERT IGNORE INTO meaning_spanish (meaning_id, spanish_term_id)
                       VALUES (%s, %s)""", (_to_str(meaning_id), _to_str(spanish_term_id)))
        cn.commit(); cur.close(); cn.close()

    # ---------- loaders (object-graph style to match your models) ----------
    def load_english_term(self, lemma: str) -> Optional[EnglishTerm]:
        cn = self._connect(); cur = cn.cursor()
        cur.execute("SELECT id, lemma, pos FROM english_term WHERE lemma=%s", (lemma,))
        row = cur.fetchone()
        if not row:
            cur.close(); cn.close(); return None

        tid, lem, pos = row
        et = EnglishTerm(term=lem, pos=PartOfSpeech(pos))
        # set DB id captured from SQL (field has init=False, but assignment is allowed)
        et.term_id = UUID(tid)

        # load meanings and their children
        cur.execute("""SELECT m.id, m.description
                       FROM meaning m
                       JOIN meaning_english me ON me.meaning_id = m.id
                       WHERE me.english_term_id = %s""", (tid,))
        for mid, desc in cur.fetchall():
            m = Meaning(description=desc, english_term=et)
            m.meaning_id = UUID(mid)
            et.add_meaning(m)

            # spanish terms
            cur2 = cn.cursor()
            cur2.execute("""SELECT st.id, st.term, st.gender
                            FROM spanish_term st
                            JOIN meaning_spanish ms ON ms.spanish_term_id = st.id
                            WHERE ms.meaning_id = %s""", (mid,))
            for sid, sp_term, g in cur2.fetchall():
                st = SpanishTerm(term=sp_term, gender=Gender(g), meaning=m)
                st.term_id = UUID(sid)
            cur2.close()

            # examples
            cur3 = cn.cursor()
            cur3.execute("""SELECT id, language, text FROM example WHERE meaning_id=%s""", (mid,))
            for eid, lang, txt in cur3.fetchall():
                ex = Example(language=lang, text=txt, meaning=m)
                ex.example_id = UUID(eid)
            cur3.close()

        cur.close(); cn.close()
        return et

    def get_meaning(self, meaning_id: UUID) -> Optional[Meaning]:
        """Rebuild a single Meaning with its EnglishTerm/SpanishTerms/Examples."""
        mid = _to_str(meaning_id)
        cn = self._connect(); cur = cn.cursor()
        # find the English term linked to this meaning
        cur.execute("""SELECT et.id, et.lemma, et.pos, m.description
                       FROM meaning m
                       JOIN meaning_english me ON me.meaning_id = m.id
                       JOIN english_term et ON et.id = me.english_term_id
                       WHERE m.id=%s""", (mid,))
        row = cur.fetchone()
        if not row:
            cur.close(); cn.close(); return None
        et_id, lemma, pos, desc = row
        et = EnglishTerm(term=lemma, pos=PartOfSpeech(pos))
        et.term_id = UUID(et_id)
        m = Meaning(description=desc, english_term=et)
        m.meaning_id = meaning_id
        et.add_meaning(m)

        # spanish terms
        cur.execute("""SELECT st.id, st.term, st.gender
                       FROM spanish_term st
                       JOIN meaning_spanish ms ON ms.spanish_term_id = st.id
                       WHERE ms.meaning_id = %s""", (mid,))
        for sid, sp_term, g in cur.fetchall():
            st = SpanishTerm(term=sp_term, gender=Gender(g), meaning=m)
            st.term_id = UUID(sid)

        # examples
        cur.execute("""SELECT id, language, text FROM example WHERE meaning_id=%s""", (mid,))
        for eid, lang, txt in cur.fetchall():
            ex = Example(language=lang, text=txt, meaning=m)
            ex.example_id = UUID(eid)

        cur.close(); cn.close()
        return m

    # Optional helpers (not used by current tests)
    def get_spanish_term(self, term_id: UUID) -> Optional[SpanishTerm]:
        # Reconstruct SpanishTerm bound to its first meaning
        sid = _to_str(term_id)
        cn = self._connect(); cur = cn.cursor()
        cur.execute("""SELECT st.term, st.gender, ms.meaning_id
                       FROM spanish_term st
                       LEFT JOIN meaning_spanish ms ON ms.spanish_term_id = st.id
                       WHERE st.id=%s LIMIT 1""", (sid,))
        row = cur.fetchone()
        if not row:
            cur.close(); cn.close(); return None
        term, g, mid = row
        if mid is None:
            # orphan term: bind to a dummy meaning-less EnglishTerm
            et = EnglishTerm(term="", pos=PartOfSpeech.OTHER)
            m = Meaning(description="", english_term=et)
        else:
            m = self.get_meaning(UUID(mid))
            if not m:
                et = EnglishTerm(term="", pos=PartOfSpeech.OTHER)
                m = Meaning(description="", english_term=et)
        st = SpanishTerm(term=term, gender=Gender(g), meaning=m)
        st.term_id = term_id
        cur.close(); cn.close()
        return st

    def get_example(self, example_id: UUID) -> Optional[Example]:
        eid = _to_str(example_id)
        cn = self._connect(); cur = cn.cursor()
        cur.execute("""SELECT e.language, e.text, e.meaning_id
                       FROM example e WHERE e.id=%s""", (eid,))
        row = cur.fetchone()
        cur.close(); cn.close()
        if not row:
            return None
        lang, txt, mid = row
        m = self.get_meaning(UUID(mid))
        if not m:
            et = EnglishTerm(term="", pos=PartOfSpeech.OTHER)
            m = Meaning(description="", english_term=et)
        ex = Example(language=lang, text=txt, meaning=m)
        ex.example_id = example_id
        return ex

    def load_meanings_for_english(self, lemma: str) -> List[Meaning]:
        et = self.load_english_term(lemma)
        return et.meanings if et else []
