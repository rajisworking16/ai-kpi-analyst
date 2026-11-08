"""Download the Olist Brazilian E-Commerce dataset from Kaggle into data/raw/.

Tries an anonymous kagglehub download first (the dataset is public). If that fails
with an auth error, retries when Kaggle credentials exist; otherwise logs a blocker.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import RAW_DIR  # noqa: E402

DATASET = "olistbr/brazilian-ecommerce"
EXPECTED_FILES = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_products_dataset.csv",
    "product_category_name_translation.csv",
]
ORDER_COLUMNS = {
    "order_id", "customer_id", "order_status", "order_purchase_timestamp",
    "order_approved_at", "order_delivered_carrier_date",
    "order_delivered_customer_date", "order_estimated_delivery_date",
}
BLOCKER = (
    "Pranav: create a free Kaggle API token at kaggle.com/settings "
    "and save it to ~/.kaggle/kaggle.json"
)


def _has_credentials() -> bool:
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    return kaggle_json.exists() or bool(os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"))


def download() -> Path:
    """Download the dataset and return the kagglehub cache directory."""
    import kagglehub

    try:
        return Path(kagglehub.dataset_download(DATASET))
    except Exception as exc:  # kagglehub raises several error types
        msg = str(exc).lower()
        if ("401" in msg or "403" in msg or "auth" in msg) and _has_credentials():
            return Path(kagglehub.dataset_download(DATASET))
        if "401" in msg or "403" in msg or "auth" in msg:
            _log_blocker()
        raise


def _log_blocker() -> None:
    progress = ROOT / "PROGRESS.md"
    text = progress.read_text() if progress.exists() else ""
    progress.write_text(f"**BLOCKER:** {BLOCKER}\n\n{text}")


def copy_csvs(src: Path, dst: Path = RAW_DIR) -> None:
    """Copy the expected CSVs (and any licence file) from the cache into dst."""
    dst.mkdir(parents=True, exist_ok=True)
    for path in src.rglob("*"):
        if path.name in EXPECTED_FILES or path.name.lower().startswith("licen"):
            shutil.copy2(path, dst / path.name)


def validate(raw_dir: Path = RAW_DIR) -> dict[str, int]:
    """Check files exist, are non-empty, and orders has expected columns."""
    counts: dict[str, int] = {}
    for name in EXPECTED_FILES:
        path = raw_dir / name
        if not path.exists():
            raise FileNotFoundError(path)
        df = pd.read_csv(path)
        if len(df) == 0:
            raise ValueError(f"{name} has 0 rows")
        if name == "olist_orders_dataset.csv":
            missing = ORDER_COLUMNS - set(df.columns)
            if missing:
                raise ValueError(f"orders file missing columns: {missing}")
        counts[name] = len(df)
    return counts


def main() -> None:
    if not all((RAW_DIR / f).exists() for f in EXPECTED_FILES):
        src = download()
        copy_csvs(src)
    for name, n in validate().items():
        print(f"{name:45s} {n:>8,d} rows")


if __name__ == "__main__":
    main()
