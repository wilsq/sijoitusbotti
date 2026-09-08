CREATE TABLE companies (
  id SERIAL PRIMARY KEY,
  ticker VARCHAR(20) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  isin VARCHAR(12),
  rss_url TEXT,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE announcements (
  id SERIAL PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES companies(id),
  source VARCHAR(50) NOT NULL,
  external_id TEXT NOT NULL,
  title TEXT NOT NULL,
  raw_content TEXT,
  published_at TIMESTAMPTZ NOT NULL,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (source, external_id)
);

CREATE TABLE summaries (
  id SERIAL PRIMARY KEY,
  announcement_id INTEGER NOT NULL REFERENCES announcements(id) UNIQUE,
  summary_text TEXT NOT NULL,
  relevance_level VARCHAR(10) NOT NULL,
  event_type VARCHAR(50),
  model_used VARCHAR(50) NOT NULL, 
  prompt_version VARCHAR(20) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  symmary_id INTEGER NOT NULL REFERENCES summaries(id),
  channel VARCHAR(20) NOT NULL,
  sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  status VARCHAR(20) NOT NULL DEFAULT 'sent'
);