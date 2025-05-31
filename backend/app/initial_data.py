#!/usr/bin/env python3

import logging

from app.db.init_db import init_db, create_sample_data
from app.db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    db = SessionLocal()
    try:
        init_db(db)
        
        # Uncomment the line below to create sample data for testing
        # create_sample_data(db)
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        db.close()


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
