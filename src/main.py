import logging
from pathlib import Path

import uvicorn

from config import settings
from config.log_conf import setup_logging

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    setup_logging(
        settings.logger,
        enqueue=True,
        project_root=Path(__file__).resolve().parent.parent,
    )
    uvicorn.run(
        "app:create_app",
        factory=True,
        host=settings.api.host,
        port=settings.api.port,
        log_level=settings.api.uc_log_level,
    )
