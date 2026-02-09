import os

# Get the base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to the database
DB_FOLDER = os.path.join(BASE_DIR, 'data')
DB_NAME = 'yle_data.db'
DB_PATH = os.path.join(DB_FOLDER, DB_NAME)

# Ensure data directory exists
os.makedirs(DB_FOLDER, exist_ok=True)