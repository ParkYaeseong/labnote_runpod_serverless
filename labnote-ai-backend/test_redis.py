# test_redis.py
from redis import Redis
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

print("✅ redis.commands.search.indexDefinition 로드 성공!")
client = Redis(host="localhost", port=6379)
print("✅ Redis 연결:", client.ping())