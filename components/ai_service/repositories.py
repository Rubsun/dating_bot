import numpy as np
from random import choice
from aiochclient import ChClient
from aiohttp import ClientSession
from common.core.config import settings


def normalize(vec):
    vec = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec.tolist()
    return (vec / norm).tolist()


class ClickHouseAsyncClient:
    def __init__(self):
        self.session = None
        self.client = None

    async def __aenter__(self):
        self.session = ClientSession()
        self.client = ChClient(
            self.session,
            url=settings.clickhouse_http_url,
            user=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            database=settings.CLICKHOUSE_DB
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def insert_vector(self, data):
        data['vector'] = normalize(data['vector'])
        query = "INSERT INTO user_vectors (userid, vector) FORMAT JSONEachRow"
        await self.client.execute(query, data)

    async def update_vector(self, userid: str, new_vector: list):
        await self.client.execute(
            f"ALTER TABLE user_vectors DELETE WHERE userid = '{userid}'"
        )
        await self.insert_vector({"userid": userid, "vector": new_vector})

    async def get_vector_by_userid(self, userid):
        sql = f"SELECT vector FROM user_vectors WHERE userid = '{userid}'"
        result = await self.client.fetch(sql)
        return result[0]["vector"] if result else None

    async def get_neighbor(self, userid, threshold=0.5):
        sql_get_vector = f"SELECT vector FROM user_vectors WHERE userid = '{userid}'"
        result = await self.client.fetch(sql_get_vector)

        if not result:
            return None

        user_vector = result[0]["vector"]
        query_vec = normalize(user_vector)
        vector_str = "[" + ",".join(map(str, query_vec)) + "]"

        sql = f'''
        SELECT 
            userid, 
            vector,
            1 - arraySum(arrayMap((x, y) -> x * y, vector, {vector_str})) AS distance
        FROM user_vectors
        WHERE 
            knnMatch(vector, {vector_str}, 'knn_index', 10) AND 
            userid != '{userid}'
        HAVING distance <= {threshold}
        ORDER BY distance ASC
        LIMIT 5
        '''

        result = await self.client.fetch(sql)
        return choice(result) if result else None