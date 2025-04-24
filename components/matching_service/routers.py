from fastapi import HTTPException, APIRouter

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute

from components.matching_service.repositories import LikeMatchRepository
from components.matching_service.schemas import LikeDislikePayload

router = APIRouter(route_class=DishkaRoute)


@router.post("/match/like")
async def create_like(
        payload: LikeDislikePayload,
        matching_repo: FromDishka[LikeMatchRepository],
):
    await matching_repo.create_like(**payload.model_dump())

    is_match = await matching_repo.create_match(payload.rater_user_id, payload.rated_user_id)
    if is_match:
        return {"status": "ok"}
    else:
        return {"status": "error"}
