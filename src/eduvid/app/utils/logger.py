import logging

logging.basicConfig(
    level=logging.INFO, # Capture INFO, WARNING, ERROR, and CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)