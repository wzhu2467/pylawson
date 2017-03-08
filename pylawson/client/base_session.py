from io import IOBase
import json
from typing import Union, Optional


class Profile:
    """Container for Lawson user profile attributes."""
    def __repr__(self):
        return self.__class__.__name__ + repr(self.__dict__)


class IosSession:
    """Base class for an Infor Lawson Connection session object."""
    def __init__(self, json_file: Union[str, IOBase] = None, lawson_server: str = None, ident_server: str = None,
                 username: str = None, password: str = None):
        self._profile = Profile()
        self._xfer_url = None
        self._params = {
            'lawson_server': lawson_server,
            'ident_server': ident_server,
            'ident_host': None,
            'username': username,
            'password': password
        }
        if json_file:
            fp = json_file if isinstance(json_file, IOBase) else open(json_file)
            json_data = json.load(fp=fp)
            self._params.update(json_data.get('lawson', {}))

    def __repr__(self):
        return self.__class__.__name__

    def __bool__(self):
        return False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def is_authenticated(self):
        return self.__bool__()

    @property
    def profile(self) -> Profile:
        return self._profile

    def get(self, url: str):
        raise NotImplementedError

    def post(self, url: str, data: dict):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def _generic_call(self, url: str, data: dict, productline_key: Optional[str]) -> str:
        """Wraps self.post to send a specific action with product line."""
        call_data = dict()
        if productline_key:
            # noinspection PyUnresolvedReferences
            call_data[productline_key] = self.profile.productline
        call_data.update(data)
        if not call_data:
            return self.get(url=url)
        return self.post(url=url, data=call_data)

    def tokens(self, data: dict):
        """Lawson ListTokens Action."""
        url = '/lawson-ios/action/ListTokens'
        productline_key = 'productLine'
        return self._generic_call(url=url, data=data, productline_key=productline_key)

    def attachments(self, data: dict):
        """Lawson ListAttachments Action."""
        url = '/lawson-ios/action/ListAttachments'
        productline_key = 'dataArea'
        return self._generic_call(url=url, data=data, productline_key=productline_key)

    def data(self, data: dict):
        """Lawson Data call."""
        url = '/servlet/Router/Data/erp'
        productline_key = 'PROD'
        return self._generic_call(url=url, data=data, productline_key=productline_key)

    def drill(self, data: dict):
        """Lawson Drill call."""
        url = '/servlet/Router/Drill/erp'
        productline_key = 'PROD'
        return self._generic_call(url=url, data=data, productline_key=productline_key)

    def transaction(self, data: dict):
        """Lawson Transaction call."""
        url = '/servlet/Router/Transaction/erp'
        productline_key = '_PDL'
        return self._generic_call(url=url, data=data, productline_key=productline_key)

    def what(self, data: dict):
        """Lawson What call."""
        url = '/servlet/What'
        return self._generic_call(url=url, data=data)
