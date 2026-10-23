-- OPCIONAL: la app crea estas tablas sola al arrancar (db.create_all()).
-- Úsalo solo si prefieres crear el esquema a mano en PostgreSQL.

CREATE TABLE IF NOT EXISTS surveys (
  id SERIAL PRIMARY KEY,
  age SMALLINT NULL,
  sex VARCHAR(40) NULL,
  main_medium VARCHAR(120) NOT NULL,
  influence_medium VARCHAR(120) NOT NULL,
  content_preference VARCHAR(160) NOT NULL,
  comments VARCHAR(1000) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_surveys_main_medium ON surveys (main_medium);
CREATE INDEX IF NOT EXISTS ix_surveys_influence_medium ON surveys (influence_medium);
CREATE INDEX IF NOT EXISTS ix_surveys_content_preference ON surveys (content_preference);
CREATE INDEX IF NOT EXISTS ix_surveys_created_at ON surveys (created_at);

CREATE TABLE IF NOT EXISTS survey_additional_media (
  id SERIAL PRIMARY KEY,
  survey_id INTEGER NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
  medium VARCHAR(120) NOT NULL,
  CONSTRAINT uq_survey_additional_medium UNIQUE (survey_id, medium)
);
CREATE INDEX IF NOT EXISTS ix_survey_additional_media_survey_id ON survey_additional_media (survey_id);
CREATE INDEX IF NOT EXISTS ix_survey_additional_media_medium ON survey_additional_media (medium);

CREATE TABLE IF NOT EXISTS strategies (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  stats_json TEXT NOT NULL,
  content TEXT NOT NULL,
  model_name VARCHAR(120) NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending'
);
CREATE INDEX IF NOT EXISTS ix_strategies_created_at ON strategies (created_at);
CREATE INDEX IF NOT EXISTS ix_strategies_status ON strategies (status);
