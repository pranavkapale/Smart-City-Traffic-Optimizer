SELECT
    id,
    speed,
    travel_time,
    data_as_of,
    geom
FROM raw_traffic
WHERE speed > 0 -- Filter out bad sensor data