# NYC Spatial Traffic Pipeline

## 📌 Overview
I built a pipeline that processes traffic points to identify congestion zones in NYC.
This project is an end-to-end Data Engineering pipeline designed to analyze real-time traffic congestion in New York City. 
It demonstrates **Geospatial Data Engineering** skills by ingesting live traffic speed data, performing spatial joins (PostGIS) to map coordinates to city boroughs, and automating the workflow.

**Key Features:**
* **ELT Architecture:** Extract, Load, and Transform pattern.
* **Geospatial Analysis:** Uses PostGIS to handle coordinate systems(`ST_GeomFromGeoJSON`,`ST_SetSRID`,`ST_MakePoint`,`ST_Multi`) and spatial joins (`ST_Contains`).
* **Infrastructure as Code:** Fully containerized using Docker.
* **Orchestration:** Automated scheduling using Dagster.

## 🏗 Architecture
1.  **Extract:** Python script hits the NYC Open Data API (Socrata).
2.  **Load:** Raw JSON is saved to a Data Lake (MinIO/S3) for durability.
3.  **Staging:** Data is loaded into PostgreSQL (PostGIS enabled).
4.  **Transform:** dbt (data build tool) performs data cleaning and spatial aggregation.
5.  **Visualize:** Final analytics are ready for tools like Kepler.gl or Superset.

## 🛠 Tech Stack
* **Language:** Python 3.9+
* **Containerization:** Docker & Docker Compose
* **Orchestration:** Dagster
* **Database:** PostgreSQL + PostGIS Extension
* **Transformation:** dbt Core
* **Storage:** MinIO (S3 Compatible)

## 🚀 How to Run

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
* Create and Add .env file with Postgres Database credentials and MinIO Configurations used in docker-compose.yml

### Steps
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/pranavkapale/Smart-City-Traffic-Optimizer
    cd Smart-City-Traffic-Optimizer
    ```

2.  **Start the infrastructure:**
    ```bash
    docker-compose up --build
    ```
    *This downloads the images for Postgres, MinIO, and Dagster and starts them.*

3.  **Access the Dashboard:**
    * Open your browser to `http://localhost:3000`.
    * Click **"Materialize All"** to trigger the pipeline manually.

4.  **Verify Data:**
    * **MinIO (Data Lake):** Go to `http://localhost:9001` (User: `minio_admin`, Pass: `minio_password`). You should see the `raw-data` bucket.
    * **Database:** Connect via DBeaver/pgAdmin using:
        * **Host:** `localhost`
        * **Port:** `5432`
        * **User:** `POSTGRES_USER` mentioned in .env file
        * **Password:** `POSTGRES_PASSWORD` mentioned in .env file
        * **Database:** `POSTGRES_DB` mentioned in .env file

## 📊 Sample Queries
Once the pipeline finishes, you can run this SQL in your database tool to see the results:

```sql
SELECT * FROM traffic_by_borough ORDER BY active_sensors DESC;
```

## Additional Info

### Reason of keeping Empty *__init__.py* 
* Although technically we can delete *__init__.py* in modern Python Projects(Python 3.3+) and the project will still work as a "Namespace Package."
* However, in our case Dagster and Python look for __init__.py to confirm that the folder is a legitimate module they can import from.
* Also, Sometimes Docker mounts volumes can cause Python to fail to find sub-modules if the __init__.py is missing. Keeping it acts as a "marker" that says "This folder is a Python package."

### Additional Helpful Docker Commands 

1.  **⏻ Shut Down the Running Services:** This stops and removes containers, networks, and volumes created by up
    ```bash
    docker-compose down
    ```
    
2.  **✔️ List down Volumes:** Docker "remembers" the older volumes even if you stop the container. So if you change Configurations from .env file in between builds this will help you to identify and delete older volumes.
    ```bash
    docker volume ls
    ```
    
3.  **🧹 Remove Single Volume:** To Remove Single Volume
    ```bash
    docker volume rm <Enter-Volume-which-needs-to-be-deleted>
    ```
    
4.  **🧹 Remove Images:** To delete the images that were built
    ```bash
    docker-compose down --rmi all
    ```
    
5.  **🗑️ Remove Volumes:** Removes volumes declared in your docker-compose.yml
    ```bash
    docker-compose down -v
    ```
    
6.  **🔄 Full Cleanup:** Remove containers, networks, images, and volumes all at once
    ```bash
    docker-compose down --rmi all -v
    ```
    
7.  **🧾 Extra Cleanup (if needed):** Remove everything Docker has created (be careful — this wipes all containers, images, volumes, and networks on your system)
    ```bash
    docker system prune -a --volumes
    ```
    💡 Tip: Use docker-compose down for normal cleanup, and only add --rmi all -v or docker system prune when you want a completely fresh slate.