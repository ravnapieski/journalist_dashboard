import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_FOLDER = os.path.join(BASE_DIR, 'data')
DB_NAME = 'yle_data.db'
DB_PATH = os.path.join(DB_FOLDER, DB_NAME)

os.makedirs(DB_FOLDER, exist_ok=True)

COLORS = ['#002858', '#054674', '#12CAB5', '#F0028D', '#8A278D', "#001631"]