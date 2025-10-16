from abc import ABC, abstractmethod
import base64
from dataclasses import dataclass
from typing import List, Any
from word_lib import WordLib
from pathlib import Path
import pickle
import time
import msgspec
from urllib.parse import urlparse
import requests

from api.api_dependency_model import APIDependencyModel
from basic.http.http_request import HTTPMethod, HTTPRequest
from basic.http.request_database import RequestDatabase
from basic.http.request_files import RequestFile
from basic.http.request_response import RequestResponse
from basic.seed import BLANK_SEED_INPUT, SeedInput
from basic.server_state import ServerState
from interface.docable import Docable


class Gatherable(ABC):
    @dataclass
    class Response:
        encoded_response: str  # base64
        db_write: list[str]
        db_read: list[str]
        file_read: list[str]
        file_write: list[str]
        table_read: list[str]
        table_write: list[str]

    def __init__(self) -> None:
        super().__init__()
        self._session = requests.session()
        self._request_responses: list[RequestResponse] = []
        self._request_dbs: list[RequestDatabase] = []
        self._request_files: list[RequestFile] = []

    @abstractmethod
    def get_final_attack_corpora(self) -> List[Any]:
        pass

    @abstractmethod
    def final_attack_weight(self) -> float:
        pass

    @abstractmethod
    def init_seeds(self) -> SeedInput:
        """
        Initialize the seed inputs for this gatherable.

        Returns:
            SeedInput_NEW_DEV: A seed. By default, returns a
            predefined global constant BLANK_SEED_INPUT_NEW_DEV.
        """
        return BLANK_SEED_INPUT

    @abstractmethod
    def api_doc(self) -> Docable:
        """
        Returns the API documentation for the corresponding vulnerability.

            Docable: The API documentation object implements Docable interface for the vulnerability.
        """
        pass

    @abstractmethod
    def get_state(self) -> ServerState:
        '''
        Returns:
            The state of the target vulnerable system
        '''
        pass

    @abstractmethod
    def attack(self):
        '''
        Attack the target vulnerable system
        '''
        pass

    @abstractmethod
    def run(self):
        '''
        Execute a series of normal user requests (using `self.make_request`)
        '''
        pass

    def session(self):
        return self._session

    def reset_session(self):
        '''
        Start a new session
        '''
        self._session.close()
        self._session = requests.session()

    def make_request(self, method: HTTPMethod, url: str, **kwargs):
        """
        Unified request handling function. If you want to use a new session, call `reset_session` before `make_request`
        Returns:
            Response of type requests.Response

        **kwargs**:
        ```
        params: _Params | None = None,
        data: _Data | None = None,
        headers: _HeadersUpdateMapping | None = None,
        cookies: RequestsCookieJar | _TextMapping | None = None,
        files: _Files | None = None,
        auth: _Auth | None = None,
        timeout: _Timeout | None = None,
        allow_redirects: bool = True,
        proxies: _TextMapping | None = None,
        hooks: _HooksInput | None = None,
        stream: bool | None = None,
        verify: _Verify | None = None,
        cert: _Cert | None = None,
        json: Any | None = None
        ```
        """
        parsed_url = urlparse(url)
        path = parsed_url.path or "/"

        response = self._session.request(method, url, **kwargs)

        files = kwargs.get('files')
        if files:
            files = {
                filename: base64.b64encode(fp.read()).decode() for filename, fp in files.items()
            }
        req = HTTPRequest(
            api=b"",
            path=path,
            method=HTTPMethod(method.upper()),
            params=kwargs.get('params'),
            json=kwargs.get('json'),
            data=kwargs.get('data'),
            headers=kwargs.get('headers'),
            files=files
        )
        response_json = response.json()
        response = Gatherable.Response(**response_json)
        serialized = base64.b64decode(response.encoded_response)
        http_response: requests.Response = pickle.loads(serialized)

        if http_response.cookies:
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname or 'localhost'
            port = parsed_url.port

            for cookie in http_response.cookies:
                if cookie.name and cookie.value:
                    # Do not set domain explicitly; let requests match automatically
                    self._session.cookies.set(
                        name=cookie.name,
                        value=cookie.value,
                        path=cookie.path or '/'
                    )

        # print("Session cookies after update:", dict(self._session.cookies))

        if http_response.headers:
            auth_headers = ['Authorization', 'Proxy-Authorization', 'X-Auth-Token', 'X-Session-Token']
            for header in auth_headers:
                if header in http_response.headers and header not in self._session.headers:
                    self._session.headers[header] = http_response.headers[header]

        self._request_responses.append(RequestResponse(
            req, http_response
        ))
        self._request_files.append(RequestFile(
            req,
            response.file_read,
            response.file_write
        ))
        self._request_dbs.append(RequestDatabase(
            req,
            response.db_read,
            response.db_write,
            response.table_read,
            response.table_write
        ))
        return http_response

    def _run(self, duration: int):
        """Run request generation until the specified time elapses"""
        start_time = time.time()
        while time.time() - start_time < duration:
            self.run()
            time.sleep(0.1)

    def generate(self, seconds: int):
        """
        Generate bins

        Parameters:
        ----------
        seconds : int
            The duration in seconds to run the data gathering process

        Returns:
        None
            The results are saved to disk files:

            - api_dependency_model.bin: The trained dependency model
            - init_words.bin: The word library
            - attacked_state.bin: The application state after attack
            - seeds.bin: Initial seeds for fuzzing
        """
        self._run(seconds)
        model = APIDependencyModel.from_doc(self.api_doc())
        # ## DEBUG
        # # with open("req+rsp.json", 'wb') as f:
        # #     f.write(msgspec.json.encode(self._request_responses))
        # with open("req+db.json", 'wb') as f:
        #     f.write(msgspec.json.encode(self._request_dbs))
        # with open("req+file.json", 'wb') as f:
        #     f.write(msgspec.json.encode(self._request_files))
        model.train(self._request_responses)
        model.train(self._request_files)
        model.train(self._request_dbs)
        model.dump_bin("api_dependency_model.bin")

        time.sleep(2)
        normal_state = self.get_state()
        wordlib = model.to_wordlib()
        for word in normal_state.to_wordlist().dictionary:
            wordlib.insert_word(word)
        wordlib.dump_bin("init_words.bin")

        self.attack()
        time.sleep(2)
        attacked_state = self.get_state()
        target_lib = WordLib(attacked_state.to_wordlist().dictionary)
        target_lib.brush(self.get_final_attack_corpora(), self.final_attack_weight())
        target_lib.dump_bin("target_wordlib.bin")
        attacked_state.dump_bin("attacked_state.bin")

        Path("seeds.bin").write_bytes(msgspec.msgpack.encode(self.init_seeds()))
