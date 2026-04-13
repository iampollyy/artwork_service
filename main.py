from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from artwork_service.database import engine, get_db, create_schema, Base
from artwork_service.models import Artwork, Artist, Categories
from artwork_service.schemas import (
    ArtworkResponse, ArtworkCreate, ArtworkUpdate, PriceUpdate
)
from artwork_service.seed import seed_data

app = FastAPI(title="ArtworkService", version="1.0.0")


@app.on_event("startup")
def startup():
    create_schema()
    Base.metadata.create_all(bind=engine)
    seed_data()


# ==================== ARTWORK ENDPOINTS ====================

@app.get("/artworks", response_model=List[ArtworkResponse])
def get_artworks(db: Session = Depends(get_db)):
    return db.query(Artwork).all()


@app.get("/artworks/{artwork_id}", response_model=ArtworkResponse)
def get_artwork(artwork_id: int, db: Session = Depends(get_db)):
    artwork = db.query(Artwork).filter(Artwork.artwork_id == artwork_id).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return artwork


@app.post("/artworks", response_model=ArtworkResponse, status_code=201)
def create_artwork(data: ArtworkCreate, db: Session = Depends(get_db)):
    artwork = Artwork(**data.model_dump())
    db.add(artwork)
    db.commit()
    db.refresh(artwork)
    return artwork


@app.put("/artworks/{artwork_id}", response_model=ArtworkResponse)
def update_artwork(artwork_id: int, data: ArtworkUpdate, db: Session = Depends(get_db)):
    artwork = db.query(Artwork).filter(Artwork.artwork_id == artwork_id).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(artwork, key, value)
    db.commit()
    db.refresh(artwork)
    return artwork


@app.put("/artworks/{artwork_id}/status")
def update_artwork_status(artwork_id: int, status: str, db: Session = Depends(get_db)):
    artwork = db.query(Artwork).filter(Artwork.artwork_id == artwork_id).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    artwork.status = status
    db.commit()
    db.refresh(artwork)
    return {"message": f"Artwork {artwork_id} status updated to {status}"}


@app.put("/artworks/{artwork_id}/price", response_model=ArtworkResponse)
def update_artwork_price(artwork_id: int, data: PriceUpdate, db: Session = Depends(get_db)):
    artwork = db.query(Artwork).filter(Artwork.artwork_id == artwork_id).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    artwork.current_price = data.current_price
    db.commit()
    db.refresh(artwork)
    return artwork