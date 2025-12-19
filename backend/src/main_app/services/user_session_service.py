from typing import List, Optional
from supabase import Client
from ..models.user_session import UserSession, UserSessionCreate, UserSessionUpdate, PaymentStatus


class UserSessionService:
    def __init__(self, db: Client):
        self.db = db
        self.table_name = "user_sessions"

    async def create(self, session_data: UserSessionCreate) -> UserSession:
        session_dict = session_data.model_dump()
        response = self.db.table(self.table_name).insert(session_dict).execute()

        if not response.data:
            raise Exception("Failed to create user session")

        return UserSession(**response.data[0])

    async def get_by_id(self, session_id: str) -> Optional[UserSession]:
        response = (
            self.db.table(self.table_name)
            .select("*")
            .eq("id", session_id)
            .execute()
        )

        if not response.data:
            return None

        return UserSession(**response.data[0])

    async def get_by_phone(self, phone_number: str) -> List[UserSession]:
        response = (
            self.db.table(self.table_name)
            .select("*")
            .eq("phone_number", phone_number)
            .order("created_at", desc=True)
            .execute()
        )

        return [UserSession(**item) for item in response.data]

    async def get_all(self, limit: int = 100, offset: int = 0,
                      payment_status: Optional[PaymentStatus] = None) -> List[UserSession]:
        query = (
            self.db.table(self.table_name)
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .offset(offset)
        )

        if payment_status:
            query = query.eq("payment_status", payment_status.value)

        response = query.execute()
        return [UserSession(**item) for item in response.data]

    async def update(self, session_id: str, update_data: UserSessionUpdate) -> Optional[UserSession]:
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

        if update_dict.get("payment_status"):
            update_dict["payment_status"] = update_dict["payment_status"].value

        response = (
            self.db.table(self.table_name)
            .update(update_dict)
            .eq("id", session_id)
            .execute()
        )

        if not response.data:
            return None

        return UserSession(**response.data[0])

    async def delete(self, session_id: str) -> bool:
        response = (
            self.db.table(self.table_name)
            .delete()
            .eq("id", session_id)
            .execute()
        )

        return len(response.data) > 0

    async def count(self, payment_status: Optional[PaymentStatus] = None) -> int:
        query = self.db.table(self.table_name).select("id", count="exact")

        if payment_status:
            query = query.eq("payment_status", payment_status.value)

        response = query.execute()
        return response.count or 0