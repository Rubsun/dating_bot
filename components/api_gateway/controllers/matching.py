import logging

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException
from grpc.aio import AioRpcError

from components.protos import matching_pb2, matching_pb2_grpc

logging.basicConfig(level=logging.INFO)

router = APIRouter(route_class=DishkaRoute)


@router.post("/users/{user_id}/find_matches")
async def find_user_matches(
    user_id: str,
    matching_stub: FromDishka[matching_pb2_grpc.MatchingStub],
):
    """
    Эндпоинт для поиска совпадений для пользователя.
    """
    logging.info("Received request to find matches for user_id: %s", user_id)
    request = matching_pb2.FindMatchesRequest(user_id=user_id)

    try:
        response = await matching_stub.FindMatches(request)
        matched_ids = list(response.matched_user_ids)
        logging.info("Found %d matches for %s", len(matched_ids), user_id)

        return {"user_id": user_id, "matches_found": matched_ids}

    except AioRpcError as e:
        logging.error("gRPC error: %s - %s", e.code(), e.details())
        raise HTTPException(
            status_code=503,
            detail=f"Matching service error: {e.details()}"
        )
    except Exception as e:
        logging.error("Unexpected error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
