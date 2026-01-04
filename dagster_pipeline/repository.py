from dagster import load_assets_from_modules, define_asset_job, ScheduleDefinition, Definitions
import assets

all_assets = load_assets_from_modules([assets])

# Job that runs everything
traffic_job = define_asset_job("process_traffic", selection="*")

# Schedule: Run every hour
hourly_schedule = ScheduleDefinition(job=traffic_job, cron_schedule="0 * * * *")

defs = Definitions(
    assets=all_assets,
    jobs=[traffic_job],
    schedules=[hourly_schedule]
)