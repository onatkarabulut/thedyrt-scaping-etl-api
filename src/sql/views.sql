CREATE OR REPLACE VIEW casestudy.top_commented_campgrounds AS
SELECT
    name,
    reviews_count,
    rating,
    split_part(address, ',', 2) AS state
FROM casestudy.campgrounds
ORDER BY reviews_count DESC
LIMIT 10;

CREATE OR REPLACE VIEW casestudy.state_rating_summary AS
SELECT
    split_part(address, ',', 2) AS state,
    COUNT(*) AS campground_count,
    AVG(rating) AS average_rating,
    AVG(price_low) AS avg_price_low,
    AVG(price_high) AS avg_price_high
FROM casestudy.campgrounds
GROUP BY state
ORDER BY average_rating DESC;

CREATE OR REPLACE VIEW casestudy.top_private_camps AS
SELECT
    name,
    operator,
    rating,
    reviews_count
FROM casestudy.campgrounds
WHERE operator = 'Private' AND reviews_count > 10
ORDER BY reviews_count DESC;
