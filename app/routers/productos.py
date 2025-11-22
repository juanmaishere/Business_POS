from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import crud, schemas
from database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.ProductoOut)
def create_producto(prod: schemas.ProductoCreate, db: Session = Depends(get_db)):
    return crud.create_producto(db, prod)

@router.get("/", response_model=list[schemas.ProductoOut])
def list_productos(db: Session = Depends(get_db)):
    return crud.get_productos(db)
