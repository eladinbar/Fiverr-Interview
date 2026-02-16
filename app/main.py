from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime
from typing import Optional

# --- Database Setup ---
# NOTE: In Docker, the host is 'db' (service name). 
# If running locally (outside Docker), change 'db' to 'localhost' and port to '5433'.
DATABASE_URL = "postgresql://app:app@db:5432/app"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- DB Model (Matches your existing table) ---
class ItemDB(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("now()"))

# --- Pydantic Schemas (For Validation) ---
class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ItemResponse(ItemCreate):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True # Allows Pydantic to read SQLAlchemy objects

# --- FastAPI App ---
app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Hello World! Sanity Check Passed."}

# 1. GET all items
@app.get("/items/", response_model=list[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    return db.query(ItemDB).all()

# 2. POST (Create) new item
@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    new_item = ItemDB(name=item.name, description=item.description)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

# 3. GET single item
@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# 4. PUT (Full Update) - Replaces the entire resource
@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item_put(item_id: int, item_in: ItemCreate, db: Session = Depends(get_db)):
    item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item.name = item_in.name
    item.description = item_in.description
    db.commit()
    db.refresh(item)
    return item

# 5. PATCH (Partial Update) - Updates only what you send
@app.patch("/items/{item_id}", response_model=ItemResponse)
def update_item_patch(item_id: int, item_in: ItemUpdate, db: Session = Depends(get_db)):
    item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item_in.name is not None:
        item.name = item_in.name
    if item_in.description is not None:
        item.description = item_in.description
    
    db.commit()
    db.refresh(item)
    return item

# 6. DELETE item
@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return {"message": "Item deleted successfully"}