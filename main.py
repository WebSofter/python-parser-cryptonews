import uvicorn
from fast_api import app
import logging
import datetime
import os
import argparse

path = os.path.dirname(os.path.realpath(__file__))
logs_folder = os.path.join(path, 'logs')
if not os.path.exists(logs_folder):
    os.mkdir(logs_folder)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename=rf"{logs_folder}/{datetime.date.today()}_logfile.txt",
                    encoding='utf-8')

logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

parser = argparse.ArgumentParser(description="Run FastAPI application with configurable port.")
parser.add_argument('--port', type=int, default=3010, help='Port to run the FastAPI application on')

if __name__ == "__main__":
    args = parser.parse_args()
    port = args.port

    logger.info(f'Starting app on port {port}')
    uvicorn.run(app, host="0.0.0.0", port=port)