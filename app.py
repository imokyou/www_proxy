# coding=utf8
from flask import Flask, request, render_template
from settings import *
from db import RedisClient

_redisdb = RedisClient()
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    proxies_source = _redisdb.get_proxies_cache()
    if not proxies_source:
        proxies_s = _redisdb.get_proxies_source(20)
        proxies_ava = _redisdb.get_proxies(10)
        proxies_source = proxies_s + proxies_ava
        _redisdb.set_proxies_cache(proxies_source)

    proxies = []
    for p in proxies_source:
        proto = p.split('://')[0]
        ip, port = p.split('://')[1].split(':')
        proxies.append({
            'ip': ip,
            'port': port,
            'proto': proto.upper()
        })
    return render_template('index.html', proxies=proxies)

@app.route("/proxy/", methods=["GET"])
def get_proxy():
    key = request.args.get('key', '')
    if key != SIGNKEY:
        return ''
    proxy = _redisdb.rand_proxy()
    return proxy

@app.route("/proxy/count/", methods=["GET"])
def count_proxy():
    proxy_len = _redisdb.proxy_len
    return str(proxy_len)


def main():
    app.run()

if __name__ == '__main__':
    main()