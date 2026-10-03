from typing import Optional, List
from sqlalchemy.orm import Session
from backend.database.models import Conversation, Message


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, conv_id: str, user_id: int) -> Optional[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(Conversation.id == conv_id, Conversation.user_id == user_id)
            .first()
        )

    def list_for_user(self, user_id: int, limit: int = 50) -> List[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .all()
        )
