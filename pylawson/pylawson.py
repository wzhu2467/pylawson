from logging import getLogger
# noinspection PyPackageRequirements
from bs4 import BeautifulSoup
from .client import IosSession as Session
from .exceptions import IosDataError

logger = getLogger(__name__)


class LawsonBase:
    """Base class for Lawson data objects."""
    def __init__(self, session: Session, **kwargs):
        self.session = session
        self._soup = None
        self._xml = None
        self.params = kwargs

    def __repr__(self):
        return self.__class__.__name__

    @property
    def xml(self):
        return self._xml

    @xml.setter
    def xml(self, value: str):
        self._soup = None
        self._xml = value

    @property
    def soup(self):
        if not self._soup:
            self._soup = BeautifulSoup(self.xml, 'html.parser')
        return self._soup

    def _error_check(self):
        if self.soup.contents[0].name == 'ERROR':
            msg = 'Infor error: [{}] {}'.format(self.soup.contents[0].attrs.get('key'), self.soup('MSG')[0].text)
            logger.error(msg=msg)
            raise IosDataError(msg)

    def query(self, **kwargs):
        raise NotImplementedError

    def upload(self, **kwargs):
        raise NotImplementedError


class What(LawsonBase):
    def query(self, jar: str='IOS.jar'):
        self.params.update({'_JAR': jar})
        # Expected response like:
        # <WHAT laversion="10.0.5.0.1093 2015-09-22 04:00:00"><JAR name="IOS.jar" path="..."><MANIFEST><![CDATA[
        # Implementation-Vendor: Lawson Software
        # Implementation-Title: IOS
        # Implementation-Version: 8-)@(#)@10.0.5.0.1093 2015-09-22 04:00:00]]></MANIFEST><LAVERSION>
        # <![CDATA[8-)@(#)@10.0.5.0.1093 2015-09-22 04:00:00]]></LAVERSION></JAR></WHAT>"""
        self.xml = self.session.what(data=self.params)
        self._error_check()
        return self

    upload = None


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
        return self

    def upload(self):
        self.params.update({'_TKN': 'AC10.1', '_RTN': 'DATA', '_TDS': 'IGNORE', '_OUT': 'XML', '_EOT': 'TRUE'})
        self.xml = self.session.transaction(data=self.params)
        self._error_check()
        return self


class Journal(LawsonBase):
    query = None

    def upload(self):
        self.params.update({'_TKN': 'GL40.2', '_RTN': 'DATA', '_TDS': 'IGNORE', '_OUT': 'XML', '_EOT': 'TRUE'})
        self.xml = self.session.transaction(data=self.params)
        self._error_check()
        return self


class JournalLine(LawsonBase):
    def query(self):
        self.params.update(
            {'FILE': 'GLTRANS', 'INDEX': 'GLTSET3', 'OUT': 'XML', 'NEXT': 'FALSE', 'MAX': '10000', 'keyUsage': 'PARAM'})
        self.xml = self.session.data(data=self.params)
        self._error_check()
        return self

    def upload(self):
        self.params.update(
            {'_TKN': 'GL40.1', '_RTN': 'DATA', '_TDS': 'IGNORE', '_OUT': 'XML', '_EOT': 'TRUE', '_INITDTL': 'TRUE'})
        self.xml = self.session.transaction(data=self.params)
        self._error_check()
        return self


class InterfaceLine(LawsonBase):
    def query(self):
        raise NotImplementedError

    def upload(self):
        raise NotImplementedError
