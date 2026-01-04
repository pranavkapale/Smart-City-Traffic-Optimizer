{{ config(materialized='table') }}

WITH traffic AS (
    SELECT * FROM {{ ref('stg_traffic') }}
),
boroughs AS (
    SELECT * FROM borough_shapes
)

SELECT
    b.borough_name,
    COUNT(t.id) as active_sensors,
    AVG(t.speed) as average_speed,
    MAX(t.speed) as max_speed,
    AVG(t.travel_time) as avg_travel_time
FROM traffic t
JOIN boroughs b
ON ST_Contains(b.geom, t.geom) -- The Spatial Magic
GROUP BY b.borough_name
ORDER BY average_speed ASC