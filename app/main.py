import os
from time import sleep
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from fastapi import FastAPI, Depends
from pydantic import BaseModel

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = "db" 
DB_PORT = "5432"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

Base = declarative_base()
class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
engine = None
for _ in range(5): 
    try:
        engine = create_engine(DATABASE_URL)
        engine.connect()
        break
    except Exception as e:
        print(f"Could not connect to database: {e}, retrying in 5 seconds...")
        sleep(5)

if engine is None:
    raise Exception("Failed to connect to the database after several retries.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine) 

class PostCreate(BaseModel):
    title: str
    content: str

class PostResponse(PostCreate):
    id: int
    class Config:
        orm_mode = True

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/posts", response_model=list[PostResponse])
def get_posts(db: sessionmaker = Depends(get_db)):
    posts = db.query(Post).all()
    return posts

@app.post("/posts", response_model=PostResponse, status_code=201)
def create_post(post: PostCreate, db: sessionmaker = Depends(get_db)):
    db_post = Post(title=post.title, content=post.content)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.get("/")
def root():
    return {"message": "Blog API is running"}
