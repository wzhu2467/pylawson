from logging import getLogger
# noinspection PyPackageRequirements
from bs4 import BeautifulSoup
from pylawson.client import IosSession

logger = getLogger(__name__)


class IosError(Exception):
    """Exceptions raised from IOS connection errors."""

    def __init__(self, message: str):
        self.message = message


class IosAuthenticationError(IosError):
    """Authentication error from connecting to IOS."""
    pass


class LawsonBase:
    """Base class for Lawson data objects."""
    resource_url = None
    productline_key = None

    def __init__(self, session: IosSession, **kwargs):
        self.session = session
        self.xml = None
        self.params = kwargs

    def __repr__(self):
        return self.__class__.__name__

    def _error_check(self):
        soup = BeautifulSoup(self.xml, 'html.parser')
        if soup.contents[0].name == 'ERROR':
            msg = 'Infor error: [{}] {}'.format(soup.contents[0].attrs.get('key'), soup('MSG')[0].text)
            logger.error(msg=msg)
            raise IosError(msg)

    def query(self, **kwargs):
        self.params.update(**kwargs)
        if self.params.get(self.productline_key) is None:
            # noinspection PyUnresolvedReferences
            self.params[self.productline_key] = self.session.profile.productline
        self.xml = self.session.post(url=self.resource_url, data=self.params)
        self._error_check()
        return self.xml

    def upload(self, **kwargs):
        self.params.update(**kwargs)
        if self.params.get(self.productline_key) is None:
            # noinspection PyUnresolvedReferences
            self.params[self.productline_key] = self.session.profile.productline
        self.xml = self.session.post(url=self.resource_url, data=self.params)
        self._error_check()
        return self.xml


class Account(LawsonBase):
    def query(self):
        raise NotImplementedError

    def upload(self):
        raise NotImplementedError


class Activity(LawsonBase):
    def query(self):
        self.params.update({'FILE': 'ACACTIVITY', 'OUT': 'XML', 'NEXT': 'FALSE', 'keyUsage': 'PARAM'})
        self.xml = self.session.data(data=self.params)
        self._error_check()
        return self.xml

    def upload(self):
        self.params.update({'_TKN': 'AC10.1', '_RTN': 'DATA', '_TDS': 'IGNORE', '_OUT': 'XML', '_EOT': 'TRUE'})
        self.xml = self.session.transaction(data=self.params)
        self._error_check()
        return self.xml


class Journal(LawsonBase):
    def query(self):
        raise NotImplementedError

    def upload(self):
        self.params.update({'_TKN': 'GL40.2', '_RTN': 'DATA', '_TDS': 'IGNORE', '_OUT': 'XML', '_EOT': 'TRUE'})
        self.xml = self.session.transaction(data=self.params)
        self._error_check()
        return self.xml


class JournalLine(LawsonBase):
    def query(self):
        self.params.update(
            {'FILE': 'GLTRANS', 'INDEX': 'GLTSET3', 'OUT': 'XML', 'NEXT': 'FALSE', 'MAX': '10000', 'keyUsage': 'PARAM'})
        self.xml = self.session.data(data=self.params)
        self._error_check()
        return self.xml

    def upload(self):
        self.params.update(
            {'_TKN': 'GL40.1', '_RTN': 'DATA', '_TDS': 'IGNORE', '_OUT': 'XML', '_EOT': 'TRUE', '_INITDTL': 'TRUE'})
        self.xml = self.session.transaction(data=self.params)
        self._error_check()
        return self.xml


class InterfaceLine(LawsonBase):
    def query(self):
        raise NotImplementedError

    def upload(self):
        raise NotImplementedError
