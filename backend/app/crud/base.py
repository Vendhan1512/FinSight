from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)

class CRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def create(self, db: Session, *, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def upsert(self, db: Session, *, obj_in: dict, index_elements: list, update_set: dict) -> ModelType:
        """
        PostgreSQL specific upsert using ON CONFLICT DO UPDATE.
        """
        stmt = insert(self.model).values(**obj_in)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=index_elements,
            set_=update_set
        )
        # Execute the statement and return the inserted/updated ID if returning() is chained,
        # but for simplicity we just execute.
        result = db.execute(upsert_stmt)
        db.commit()
        return result
