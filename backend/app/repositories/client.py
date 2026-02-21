from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.client import Client
from app.repositories.base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    def __init__(self, db: AsyncSession):
        super().__init__(Client, db)

    async def get_by_business_name(self, name: str) -> Client | None:
        result = await self.db.execute(
            select(Client).where(Client.name_of_business == name)
        )
        return result.scalar_one_or_none()
