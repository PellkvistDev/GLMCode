"""Logging configuration for GLM Code."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from .config import CONFIG_DIR

LOG_LEVEL = os.environ.get("GLM_LOG_LEVEL", "INFO").upper()
LOG_FILE = CONFIG_DIR / "glmcode.log"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("glmcode")
