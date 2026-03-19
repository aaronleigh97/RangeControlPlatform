import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()  # reads .env if present

@dataclass(frozen=True)
class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Range Control Platform")
    ENV: str = os.getenv("ENV", "local")  # local | jd
    DEBUG: bool = os.getenv("DEBUG", "1") == "1"

    # future: BigQuery project/datasets (safe placeholders)
    BQ_PROJECT: str = os.getenv("BQ_PROJECT", "")
    BQ_DATASET: str = os.getenv("BQ_DATASET", "")
    BQ_BRANCH_SOURCE_TABLE: str = os.getenv(
        "BQ_BRANCH_SOURCE_TABLE",
        "jd-gcp-prd-dl-structured-np.PDS_STAGE.ORSTBRCH",
    )

settings = Settings()
