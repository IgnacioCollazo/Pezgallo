from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from typing import List
import models, schemas

router = APIRouter(prefix="/menu", tags=["menu"])

@router.get("/", response_model=List[schemas.ItemMenuOut])
def listar_menu(db: Session = Depends(get_db)):
    return db.query(models.ItemMenu).filter(models.ItemMenu.disponible == True).all()