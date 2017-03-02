from io import IOBase
import json
from logging import getLogger
from typing import Union
# noinspection PyPackageRequirements
from bs4 import BeautifulSoup

logger = getLogger(__name__)


class IosError(Exception):
    """Exceptions raised from IOS connection errors."""
    def __init__(self, message: str):
        self.message = message


class IosAuthenticationError(IosError):
    """Authentication error from connecting to IOS."""
    pass


class Profile:
    def __repr__(self):
        return self.__class__.__name__ + repr(self.__dict__)


class IosSession:
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
    def profile(self):
        return self._profile

    def get(self, url: str):
        raise NotImplementedError

    def post(self, url: str, data: dict):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError


class LawsonBase:
    def __init__(self):
        pass

    def __repr__(self):
        return self.__class__.__name__

    def query(self):
        pass

    def upload(self):
        pass


# Please do not use Ios, use pylawson.client.SamlSession directly. This is deprecated.
class __OriginalIosDoNotUseBeingRefactored:
    # noinspection PyUnresolvedReferences
    def call(self, call_type: str, params: dict) -> BeautifulSoup:
        logger.warning('Ios.call deprecated')
        if call_type not in ('Data', 'Transaction', 'Drill', 'Attach', 'Tokens'):
            raise IosError('Invalid call type.')
        if call_type in ('Data', 'Drill') and params.get('PROD') is None:
            params['PROD'] = self.profile.productline
        elif call_type == 'Transaction' and params.get('_PDL') is None:
            params['_PDL'] = self.profile.productline
        elif call_type == 'Attach' and params.get('dataArea') is None:
            params['dataArea'] = self.profile.productline
        elif call_type == 'Tokens' and params.get('productLine') is None:
            params['productLine'] = self.profile.productline
        if call_type in ('Data', 'Drill', 'Transaction'):
            url = '/servlet/Router/{}/erp'.format(call_type)
        elif call_type == 'Attach':
            url = '/lawson-ios/action/ListAttachments'
        elif call_type == 'Tokens':
            url = '/lawson-ios/action/ListTokens'
        # noinspection PyUnboundLocalVariable
        soup = BeautifulSoup(self.post(url, data=params), 'html.parser')
        if soup.contents[0].name == 'ERROR':
            msg = 'Infor error: [{}] {}'.format(soup.contents[0].attrs.get('key'), soup('MSG')[0].text)
            logger.error(msg=msg)
            raise IosError(msg)
        return soup

    def gl40_2(self, params: dict) -> BeautifulSoup:
        payload = {'_TKN': 'GL40.2', '_RTN': 'DATA', '_TDS': 'IGNORE', '_OUT': 'XML', '_EOT': 'TRUE'}
        payload.update(params)
        return self.call('Transaction', payload)

    def gl40_1(self, params: dict) -> BeautifulSoup:
        payload = {'_TKN': 'GL40.1', '_RTN': 'DATA', '_TDS': 'IGNORE', '_OUT': 'XML', '_EOT': 'TRUE',
                   '_INITDTL': 'TRUE'}
        payload.update(params)
        return self.call('Transaction', payload)

    def gl90(self, params: dict) -> BeautifulSoup:
        payload = {'FILE': 'GLTRANS', 'INDEX': 'GLTSET3', 'OUT': 'XML', 'NEXT': 'FALSE',
                   'MAX': '10000', 'keyUsage': 'PARAM'}
        payload.update(params)
        return self.call('Data', payload)

    def ac10_inquire(self, params: dict) -> BeautifulSoup:
        payload = {'FILE': 'ACACTIVITY', 'OUT': 'XML', 'NEXT': 'FALSE', 'keyUsage': 'PARAM'}
        payload.update(params)
        return self.call('Data', payload)

    def ac10_add(self, params: dict) -> BeautifulSoup:
        payload = {'_TKN': 'AC10.1', '_RTN': 'DATA', '_TDS': 'IGNORE', '_OUT': 'XML', '_EOT': 'TRUE'}
        payload.update(params)
        return self.call('Transaction', payload)
