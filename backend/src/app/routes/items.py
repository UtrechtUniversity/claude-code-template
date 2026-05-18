from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Item
from app.schemas import ItemCreate, ItemRead

router = APIRouter()


@router.get("/", response_model=list[ItemRead])
async def list_items(session: AsyncSession = Depends(get_session)) -> list[Item]:
    result = await session.execute(select(Item))
    return list(result.scalars().all())


@router.post("/", response_model=ItemRead, status_code=201)
async def create_item(body: ItemCreate, session: AsyncSession = Depends(get_session)) -> Item:
    item = Item(title=body.title)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item
