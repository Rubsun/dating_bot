import clickhouse_connect

from common.core.config import settings

client = clickhouse_connect.get_client(
    host=settings.CLICKHOUSE_HOST,
    port=settings.CLICKHOUSE_HTTP_PORT,
    username=settings.CLICKHOUSE_USER,
    password=settings.CLICKHOUSE_PASSWORD,
    database=settings.CLICKHOUSE_DB
)

client.command('''
CREATE TABLE IF NOT EXISTS user_vectors (
    userid UUID,
    vector Array(Float32)
) ENGINE = MergeTree()
ORDER BY userid
''')

try:
    client.command('''
    ALTER TABLE user_vectors
    ADD INDEX knn_index vector TYPE knn(5, 10, 'CosineDistance') GRANULARITY 1
    ''')
except Exception as e:
    print("Индекс knn_index уже существует")