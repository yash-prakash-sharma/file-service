from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class FileRecord(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    sys_filename = Column(String(255), unique=True, index=True, nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100))
    file_path = Column(String(500), nullable=False)
    size = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
