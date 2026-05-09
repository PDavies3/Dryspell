import os
import yaml
from datetime import datetime, timezone, timedelta
import earthaccess

# Load central configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

# DYNAMIC OVERRIDE: If running on GitHub Actions, bypass the yaml path!
if os.environ.get("GITHUB_ACTIONS") == "true":
    RAW_DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "../data/raw"))
else:
    RAW_DATA_DIR = config["data_path"]
os.makedirs(RAW_DATA_DIR, exist_ok=True)

def download_latest_imerg(days_back=5):
    """
    Checks NASA Earthdata for the latest daily IMERG granules and downloads missing files.
    """
    print(f"[{datetime.now()}] Starting IMERG auto-downloader...")
    
    try:
        # Authenticate using your pre-saved ~/.netrc credentials
        earthaccess.login()
    except Exception as e:
        print(f"Authentication failed: {e}")
        return False

    # Define timezone-aware temporal query window to avoid Python 3.13 deprecation warnings
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    print(f"Searching for {config['short_name']} (v{config['version']}) from {start_str} to {end_str}...")

    results = earthaccess.search_data(
        short_name=config["short_name"],
        version=config["version"],
        temporal=(start_str, end_str)
    )

    if not results:
        print("No new files found online.")
        return False

    print(f"Found {len(results)} remote files. Commencing download...")
    
    # Download files (earthaccess automatically skips already existing files)
    downloaded_files = earthaccess.download(results, local_path=RAW_DATA_DIR)
    
    print(f"[{datetime.now()}] Download process finished.")
    return len(downloaded_files) > 0

if __name__ == "__main__":
    download_latest_imerg()
