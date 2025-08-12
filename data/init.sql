CREATE DATABASE IF NOT EXISTS medical
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE medical;

CREATE TABLE IF NOT EXISTS english_term (
  id CHAR(36) NOT NULL,
  lemma NVARCHAR(100) NOT NULL,
  pos VARCHAR(20) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_lemma (lemma)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS spanish_term (
  id CHAR(36) NOT NULL,
  term NVARCHAR(100) NOT NULL,
  gender VARCHAR(10) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_spanish_term (term)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS meaning (
  id CHAR(36) NOT NULL,
  description TEXT NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS example (
  id CHAR(36) NOT NULL,
  meaning_id CHAR(36) NOT NULL,
  language CHAR(2) NOT NULL,
  text TEXT NOT NULL,
  PRIMARY KEY (id),
  KEY fk_example_meaning (meaning_id),
  CONSTRAINT fk_example_meaning FOREIGN KEY (meaning_id)
    REFERENCES meaning(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS meaning_english (
  meaning_id CHAR(36) NOT NULL,
  english_term_id CHAR(36) NOT NULL,
  PRIMARY KEY (meaning_id, english_term_id),
  KEY fk_me_et (english_term_id),
  CONSTRAINT fk_me_m  FOREIGN KEY (meaning_id)      REFERENCES meaning(id)       ON DELETE CASCADE,
  CONSTRAINT fk_me_et FOREIGN KEY (english_term_id) REFERENCES english_term(id)  ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS meaning_spanish (
  meaning_id CHAR(36) NOT NULL,
  spanish_term_id CHAR(36) NOT NULL,
  PRIMARY KEY (meaning_id, spanish_term_id),
  KEY fk_ms_st (spanish_term_id),
  CONSTRAINT fk_ms_m  FOREIGN KEY (meaning_id)      REFERENCES meaning(id)        ON DELETE CASCADE,
  CONSTRAINT fk_ms_st FOREIGN KEY (spanish_term_id) REFERENCES spanish_term(id)   ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET @en_id = UUID();
SET @m_id  = UUID();
SET @es_id = UUID();
SET @ex1   = UUID();
SET @ex2   = UUID();

INSERT INTO english_term (id, lemma, pos) VALUES (@en_id, 'lesion', 'noun');
INSERT INTO meaning (id, description) VALUES (@m_id, 'Pathological change; abnormal tissue');
INSERT INTO spanish_term (id, term, gender) VALUES (@es_id, 'lesión', 'f');
INSERT INTO meaning_english (meaning_id, english_term_id) VALUES (@m_id, @en_id);
INSERT INTO meaning_spanish (meaning_id, spanish_term_id) VALUES (@m_id, @es_id);
INSERT INTO example (id, meaning_id, language, text) VALUES
(@ex1, @m_id, 'en', 'The MRI showed a suspicious brain lesion.'),
(@ex2, @m_id, 'es', 'La resonancia mostró una lesión sospechosa en el cerebro.');
