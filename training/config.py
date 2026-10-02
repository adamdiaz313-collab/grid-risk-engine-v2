from pathlib import Path


# ============================================
# PROJECT PATHS
# ============================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

EAGLEI_RAW_DIR = RAW_DIR / "eaglei"
EAGLEI_INTERIM_DIR = INTERIM_DIR / "eaglei"
EAGLEI_STANDARDIZED_DIR = EAGLEI_INTERIM_DIR / "standardized"
EAGLEI_HOURLY_DIR = EAGLEI_INTERIM_DIR / "hourly"

MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
METRICS_DIR = REPORTS_DIR / "metrics"


# ============================================
# DATA SOURCE SETTINGS
# ============================================

EAGLEI_FIGSHARE_ARTICLE_ID = 24237376
EAGLEI_FIGSHARE_API_URL = (
    f"https://api.figshare.com/v2/articles/{EAGLEI_FIGSHARE_ARTICLE_ID}"
)


# ============================================
# MODEL / DATA SETTINGS
# ============================================

RANDOM_SEED = 42

START_YEAR = 2014
END_YEAR = 2025

TIME_RESOLUTION = "1h"
FORECAST_HORIZON_HOURS = 6

TIMEZONE = "UTC"


# ============================================
# DIRECTORY SETUP
# ============================================

DIRECTORIES = [
    DATA_DIR,
    RAW_DIR,
    INTERIM_DIR,
    PROCESSED_DIR,
    EAGLEI_RAW_DIR,
    EAGLEI_INTERIM_DIR,
    EAGLEI_STANDARDIZED_DIR,
    EAGLEI_HOURLY_DIR,
    MODELS_DIR,
    REPORTS_DIR,
    FIGURES_DIR,
    METRICS_DIR,
]


def ensure_project_directories():
    """
    Create the standard Grid Risk Engine V2 directories
    if they do not already exist.
    """
    for directory in DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    ensure_project_directories()

    print("Grid Risk Engine V2 directories are ready.")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Forecast horizon: {FORECAST_HORIZON_HOURS} hours")
    print(f"Time resolution: {TIME_RESOLUTION}")
    print(f"Data years: {START_YEAR}-{END_YEAR}")
