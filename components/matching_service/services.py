import logging

from grpc.aio import ServicerContext

from components.protos import matching_pb2, matching_pb2_grpc

logging.basicConfig(level=logging.INFO)


class MatchingServicer(matching_pb2_grpc.MatchingServicer):
    async def FindMatches(
        self,
        request: matching_pb2.FindMatchesRequest,
        context: ServicerContext
    ) -> matching_pb2.FindMatchesResponse:

        user_id = request.user_id
        logging.info(f"FindMatches request received for user_id: {user_id}")

        # business logic
        matched_ids = [f"matched_user_{i}" for i in range(1, 4)]

        logging.info(f"Found matches for {user_id}: {matched_ids}")
        return matching_pb2.FindMatchesResponse(matched_user_ids=matched_ids)
