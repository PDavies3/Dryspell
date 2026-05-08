import os
import time
import logging
import yaml
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from downloader import download_latest_imerg
from processor import run_processor

# Load configs to locate folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

LOG_FILE = os.path.join(BASE_DIR, config["log_dir"], "pipeline.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Configure background logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def run_pipeline_cycle():
    logging.info("--- Starting Daily Scheduled Pipeline Cycle ---")
    try:
        # Step 1: Check and download new NetCDFs
        logging.info("Calling IMERG Downloader...")
        new_data_found = download_latest_imerg(days_back=7)
        
        # Step 2: If we pulled new files, rebuild dry spell plots
        if new_data_found:
            logging.info("New data grabbed. Triggering Processing Engine...")
            plots_saved = run_processor()
            logging.info(f"Re-processed files. Generated {len(plots_saved)} plots.")
        else:
            logging.info("No new files found at GES DISC. Skipping process calculations.")
            
    except Exception as e:
        logging.error(f"Pipeline crashed during execution: {e}", exc_info=True)
    logging.info("--- Cycle Complete ---")

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    
    # Scheduled to run every single day at 03:00 AM local system time
    scheduler.add_job(run_pipeline_cycle, 'cron', hour=3, minute=0)
    
    logging.info("Background Scheduler initialized. Running pipeline once on start...")
    run_pipeline_cycle()  # Run once immediately on start to check status
    
    scheduler.start()
    logging.info("Scheduler monitoring active. Press Ctrl+C to stop daemon.")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("Background Scheduler gracefully shut down.")