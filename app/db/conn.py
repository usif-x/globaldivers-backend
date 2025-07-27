from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os
from dotenv import load_dotenv

load_dotenv()

THIS_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_DIR = os.path.dirname(THIS_PATH)
ROOT_DIR = os.path.dirname(BASE_DIR)

DB_HOST = os.environ.get("DB_HOST")
DB_USERNAME = os.environ.get("DB_USERNAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")

DB_URI = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

DATABASE_URL = os.environ.get("DB_URI")


engine = create_engine(DB_URI, echo=True)


SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
  pass