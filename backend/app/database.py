import os

from sqlalchemy import create_engine


DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{os.getenv('POSTGRES_USER', 'opspilot')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'opspilot_dev_password')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'opspilot')}"
)


engine = create_engine(DATABASE_URL)