import requests
import json
import psycopg2
from dagster import asset, MaterializeResult

from resources import get_s3_client, get_db_connection

# --- CONFIGURATION ---
# NYC Open Data API (Traffic Speeds)
TRAFFIC_API_URL = "https://data.cityofnewyork.us/resource/i4gi-tjb9.json?$limit=500"
# NYC Planning Dept (Borough Boundaries GeoJSON)
BOROUGH_GEOJSON_URL = "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/NYC_Borough_Boundary/FeatureServer/0/query?where=1=1&outFields=*&outSR=4326&f=geojson"

# --- ASSET 1: EXTRACT (API -> MinIO) ---
@asset
def extract_traffic_data():
    """Fetches traffic data and saves to MinIO (S3)"""
    # 1. Fetch Data
    response = requests.get(TRAFFIC_API_URL)
    data = response.json()

    # 2. Upload to MinIO
    s3 = get_s3_client()
    try:
        s3.create_bucket(Bucket='raw-data')
    except:
        pass  # Bucket likely exists

    s3.put_object(
        Bucket='raw-data',
        Key='traffic/latest.json',
        Body=json.dumps(data)
    )
    return MaterializeResult(metadata={"record_count": len(data)})

# --- ASSET 2: LOAD (borough GeoJSON -> PostGIS) ---
@asset
def load_borough_geojson():
    """One-Time Fetch of Borough Boundaries from geojson and saves into Postgres"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Create Table for Boroughs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS borough_shapes (
            borough_name VARCHAR,
            geom geometry(MULTIPOLYGON, 4326)
        )
    """)

    # Check if empty
    cur.execute("SELECT COUNT(*) FROM borough_shapes")
    if cur.fetchone()[0] == 0:
        print("Fetching Borough GeoJSON")
        data = requests.get(BOROUGH_GEOJSON_URL).json()

        for feature in data['features']:
            props = feature['properties']
            name = props['BoroName']
            # Convert GeoJSON geometry to PostGIS string representation
            geojson_str = json.dumps(feature['geometry'])

            # Added MultiPolygon Support using ST_Multi
            # As Point being inside a MultiPolygon works exactly the same way as being inside a Polygon using the ST_Contains function, It won't break any functionality
            cur.execute("""
                INSERT INTO borough_shapes (borough_name, geom)
                VALUES (%s, ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)))
            """, (name, geojson_str))

        conn.commit()

    conn.close()
    return MaterializeResult(metadata={"status": "Loaded"})

# --- ASSET 3: LOAD (MinIO -> Postgres) ---
@asset(deps=[extract_traffic_data])
def traffic_table():
    """Reads JSON from MinIO and loads into PostGIS"""

    # 1. Read from MinIO
    s3 = get_s3_client()
    obj = s3.get_object(Bucket='raw-data', Key='traffic/latest.json')
    data = json.loads(obj['Body'].read())

    # 2. Connect to Postgres
    conn = get_db_connection()
    cur = conn.cursor()

    # 3. Create Raw Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_traffic (
            id VARCHAR,
            speed FLOAT,
            travel_time FLOAT,
            geom geometry(Point, 4326),
            data_as_of TIMESTAMP
        );
    """)

    # Clear old data for fresh start
    cur.execute("TRUNCATE TABLE raw_traffic;")

    # 4. Insert Data (Converting Text Lat/Lon to Geometry)
    # The API returns "link_points" as a string: "40.7,-73.9 40.8,-74.0 ..."
    # We just want the FIRST point to represent the sensor location.
    for row in data:
        points_str = row.get('link_points', '')
        if not points_str:
            continue

        # Take first Pair
        first_point = points_str.split(',')[0]
        if ',' not in first_point:
            continue

        lat, lon = first_point.split(',')

        cur.execute("""
            INSERT INTO raw_traffic (id, speed, travel_time, geom, timestamp)
            VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s), 4326), %s)
        """, (
            row.get('id'),
            float(row.get('speed'),0),
            float(row.get('travel_time'),0),
            (float(lon), float(lat)),
            row.get('timestamp')    # PostGIS uses (Lon, Lat) Order
        ))

    conn.commit()
    conn.close()
    return MaterializeResult(metadata={"status": "Traffic Loaded"})