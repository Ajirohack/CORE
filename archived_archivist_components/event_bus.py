"""
Event bus using Redis pub/sub for async task dispatch.
"""
import redis
import threading

class EventBus:
    def __init__(self, redis_url="redis://localhost:6379/0"):
        self.redis = redis.Redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()

    def publish(self, channel, message):
        self.redis.publish(channel, message)

    def subscribe(self, channel, callback):
        def listen():
            self.pubsub.subscribe(channel)
            for msg in self.pubsub.listen():
                if msg['type'] == 'message':
                    callback(msg['data'])
        thread = threading.Thread(target=listen, daemon=True)
        thread.start()
# ...existing code...
