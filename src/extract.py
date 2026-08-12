"""Extract raw flight records from a CSV source."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd


LOGGER = logging.getLogger("airport_pipeline.extract")


def extract_csv(file_path: Path) -> pd.DataFrame:
    """Read a non-empty CSV file and return its records as a DataFrame."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {file_path}")
    if file_path.stat().st_size == 0:
        raise ValueError(f"Input file is empty: {file_path}")

    dataframe = pd.read_csv(file_path, dtype=str, keep_default_na=True)
    if dataframe.empty:
        raise ValueError(f"Input CSV contains no records: {file_path}")

    LOGGER.info("Extracted %d rows and %d columns", *dataframe.shape)
    return dataframe

