(domp-env) lando@jellynose:~/projects/fromperdomp-poc/implementations/reference/python$ source domp-env/bin/activate && python3 web_api.py
/home/lando/projects/fromperdomp-poc/implementations/reference/python/web_api.py:236: DeprecationWarning:
        on_event is deprecated, use lifespan event handlers instead.

        Read more about it in the
        [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).

  @app.on_event("startup")
INFO:     Will watch for changes in these directories: ['/home/lando/projects/fromperdomp-poc/implementations/reference/python']
ERROR:    [Errno 98] Address already in use