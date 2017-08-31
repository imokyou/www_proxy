# coding=utf8
import traceback
import urllib
import json
import redis
from settings import *


class RedisClient(object):

    def __init__(self):
        try:
            if REDIS['password']:
                redis_pool = redis.ConnectionPool(host=REDIS['host'], port=REDIS['port'], password=REDIS['password'], db=REDIS['db'])
            else:
                redis_pool = redis.ConnectionPool(host=REDIS['host'], port=REDIS['port'], db=REDIS['db'])
            self._db = redis.Redis(connection_pool=redis_pool)
        except:
            logging.info('connect redis error')
        self._proxy = 'proxy'
        self._proxy_source = 'proxy:source'
        self._proxy_cache = 'proxy:cache'

    def add_proxy(self, proxy):
        if not proxy:
            return None
        proxies = self.get_allproxy()
        if proxy in proxies:
            return None
        self._db.lpush(self._proxy, proxy)
    
    def add_proxies(self, proxies):
        if not proxies:
            return None
        for u in proxies:
            self.add_proxies(proxies)

    def add_proxy_source(self, proxy):
        if not proxy:
            return None
        self._db.sadd(self._proxy_source, proxy)

    def add_proxies_source(self, proxies):
        if not proxies:
            return None
        for u in proxies:
            self.add_proxy_source(u)

    def rand_proxy(self):
        try:
            proxy = self._db.rpop(self._proxy)
            self.add_proxy(proxy)
            return proxy
        except:
            pass
        return None

    def remove_proxy(self, proxy):
        try:
            return self._db.lrem(self._proxy, proxy)
        except:
            traceback.print_exc()

    def get_proxies(self, count=1):
        proxies = self._db.lrange(self._proxy, 0, count)
        return proxies
        
    def get_allproxy(self):
        proxies = self._db.lrange(self._proxy, 0, -1)
        return proxies

    def get_proxies_source(self, count=1):
        proxies = self._db.srandmember(self._proxy_source, count)
        return proxies

    def get_proxies_cache(self):
        proxies = self._db.get(self._proxy_cache)
        if proxies:
            return json.loads(proxies)
        return []

    def set_proxies_cache(self, proxies):
        proxies = json.dumps(proxies)
        self._db.set(self._proxy_cache, proxies)
        self._db.expire(self._proxy_cache, 60*15)

    @property
    def proxy_len(self):
        return self._db.llen(self._proxy)


if __name__ == '__main__':
    pass
