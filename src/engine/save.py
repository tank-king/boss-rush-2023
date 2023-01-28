import json
import platform
import sys
from urllib.parse import urlencode

INFO_GITHUB_LINK = "https://tank-king.github.io/projects/games/bug_invaders.json"


class WASMFetch:
    """
    WASM compatible request handler
    auto-detects emscripten environment and sends requests using JavaScript Fetch API
    """
    GET = 'GET'
    POST = 'POST'
    _js_code = ''
    _init = False

    def __init__(self):
        self.is_web = True if sys.platform == 'emscripten' else False
        if not self._init:
            self.init()
        self.debug = True
        self.get_result = None
        self.post_result = None
        self.domain = "null"
        if not self.is_web:
            try:
                import requests
                self.requests = requests
                try:
                    self.domain = requests.get(INFO_GITHUB_LINK, timeout=0.1).json()['leaderboard_url']
                except requests.ReadTimeout:
                    pass
                except requests.RequestException:
                    pass
            except ImportError:
                pass
        else:
            self.window.eval('window.get_response = "null";')
            self.window.eval('window.post_response = "null";')
            self.window.eval('window.domain = "null"')
            self.window.eval(
                'window.http_get = function(url){ window.get_response = "loading"; fetch(url).then( function(response) {return response.json();}).then(function(data) { window.get_response = JSON.stringify(data);}).catch(function(err) { window.get_response = err; });}')
            self.window.eval(
                """window.http_post = function(url, data){ window.post_response = "loading"; fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json',}, body: JSON.stringify(data)}).then( function(response) {return response.json();}).then(function(data) { window.post_response = JSON.stringify(data);}).catch(function(err) { window.post_response = err; });}""")

            self.window.eval(
                """fetch(" """ + INFO_GITHUB_LINK + """ ").then(function(response){return response.json();}).then(function(data) {window.domain = data.leaderboard_url}).catch(function(err) {window.domain = err})""")

    def init(self):
        self.is_web = sys.platform in ('emscripten', 'wasi')
        if self.is_web:
            platform.document.body.style.background = "#511309"

    @property
    def window(self):
        if self.is_web:
            return platform.window

    def get_domain(self):
        if self.is_web:
            return self.window.domain
        else:
            return self.domain

    @staticmethod
    def print(*args, default=True):
        try:
            for i in args:
                platform.window.console.log(i)
        except AttributeError:
            pass
        except Exception as e:
            return e
        if default:
            print(*args)

    def get_request(self, url, params=None, doseq=False):
        if params is None:
            params = {}
        if self.is_web:
            query_string = urlencode(params, doseq=doseq)
            final_url = url + "?" + query_string
            self.window.eval(f'window.http_get("{final_url}")')
        else:
            self.get_result = self.requests.get(url, params=params).text
        return self.get_result

    def post_request(self, url, data=None):
        if data is None:
            data = {}
        if self.is_web:
            self.window.eval(f'window.http_post("{url}", {json.dumps(data)})')
            print(json.dumps(data))
        else:
            self.post_result = self.requests.post(url, data).text
        return self.post_result

    def set_get_response(self, value):
        if self.is_web:
            self.window.eval(f"window.get_response = {value.__repr__()}")
        else:
            self.get_result = value

    def get_response(self):
        if self.is_web:
            return self.window.get_response
        else:
            return self.get_result

    def set_post_response(self, value):
        if self.is_web:
            self.window.eval(f"window.post_response = {value.__repr__()}")
        else:
            self.post_result = value

    def post_response(self):
        if self.is_web:
            return str(self.window.post_response).__repr__()
        else:
            return self.post_result

    def request_leaderboard(self):
        self.get_request(self.get_domain() + '/leaderboards/get', params={
            'developer': 'tankking',
            'leaderboard': 'bug-invaders',
        })

    def post_score(self, name, score, validation_data=''):
        domain = self.get_domain()
        return self.post_request(domain + '/leaderboards/post/', data={
            'developer': 'tankking',
            'leaderboard': 'bug-invaders',
            'name': name,
            'score': score,
            'validation_data': validation_data
        })
