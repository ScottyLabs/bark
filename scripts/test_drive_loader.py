"""
Script to test Google Drive loader.
Usage: python scripts/test_drive_loader.py [path/to/credentials.json]
"""

import sys
import os
import logging
from pathlib import Path

# Add src to python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from bark.context.drive_loader import DriveLoader
from bark.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    if len(sys.argv) > 1:
        creds_file = sys.argv[1]
    else:
        # Try to get from settings or default
        settings = get_settings()
        creds_file = settings.google_drive_credentials_file

    if not os.path.exists(creds_file):
        logger.error(f"Credentials file not found: {creds_file}")
        logger.info("Please provide path to credentials.json as argument or in .env")
        return

    logger.info(f"Testing DriveLoader with credentials: {creds_file}")
    if settings.google_drive_folder_id:
        logger.info(f"Using Folder ID: {settings.google_drive_folder_id}")
    else:
        logger.info("No Folder ID configured (searching root/all drives)")
    
    loader = DriveLoader(
        credentials_file=creds_file,
        folder_id=settings.google_drive_folder_id
    )
    
    try:
        # Test 1: Fetch metadata
        logger.info("Fetching metadata...")
        metadata = loader.fetch_file_metadata()
        logger.info(f"Found {len(metadata)} files available")
        
        if not metadata:
            logger.warning("No files found. Check your Drive permissions or folder content.")
            return

        # Test 2: Load first 3 files
        file_ids = list(metadata.keys())[:3]
        logger.info(f"Loading content for first {len(file_ids)} files: {file_ids}")
        
        chunks = loader.load(file_ids=file_ids)
        logger.info(f"Loaded {len(chunks)} chunks")
        
        for chunk in chunks:
            logger.info("--- Chunk ---")
            logger.info(f"ID: {chunk.id}")
            logger.info(f"Source: {chunk.metadata.get('page')} ({chunk.metadata.get('source')})")
            logger.info(f"Content preview: {chunk.content[:200]}...")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
