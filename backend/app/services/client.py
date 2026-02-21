from uuid import UUID
from app.repositories.client import ClientRepository
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse


class ClientService:
    def __init__(self, repo: ClientRepository):
        self.repo = repo

    async def get_client(self, id: UUID) -> ClientResponse | None:
        client = await self.repo.get_by_id(id)
        return ClientResponse.model_validate(client) if client else None

    async def get_all_clients(self, skip: int = 0, limit: int = 100) -> list[ClientResponse]:
        clients = await self.repo.get_all(skip, limit)
        return [ClientResponse.model_validate(c) for c in clients]

    async def get_by_business_name(self, name: str) -> ClientResponse | None:
        client = await self.repo.get_by_business_name(name)
        return ClientResponse.model_validate(client) if client else None

    async def create_client(self, data: ClientCreate) -> ClientResponse:
        client = await self.repo.create(**data.model_dump(exclude_unset=True))
        return ClientResponse.model_validate(client)

    async def update_client(self, id: UUID, data: ClientUpdate) -> ClientResponse | None:
        client = await self.repo.update(id, **data.model_dump(exclude_unset=True))
        return ClientResponse.model_validate(client) if client else None

    async def delete_client(self, id: UUID) -> bool:
        return await self.repo.delete(id)
