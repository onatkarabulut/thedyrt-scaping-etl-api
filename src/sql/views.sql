CREATE VIEW raw_counts AS
SELECT
  date_trunc('hour', received_at) AS hour,
  COUNT(*) AS total
FROM staging.raw_campgrounds
GROUP BY 1;

CREATE VIEW enriched_counts AS
SELECT
  date_trunc('hour', enriched_at) AS hour,
  COUNT(*) AS total
FROM staging.enriched_campgrounds
GROUP BY 1;

CREATE VIEW load_stats AS
SELECT
  date_trunc('day', loaded_at) AS day,
  COUNT(*) AS total_loaded,
  AVG(load_duration) AS avg_time_secs
FROM core.load_history
GROUP BY 1;
