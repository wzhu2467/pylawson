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


class Gen(LawsonBase):
    """Add-in startup queries to get environment data"""
    # Add-Ins start up with these queries:
    # /servlet/Router/Data/Erp?PROD=GEN&FILE=PROJECT
    #   no data?
    # PROD=GEN&FILE=SYSTEM&INDEX=STMSET1&KEY=LSAPPS&FIELD=SystemCode;SysName
    #   data as "GL","General Ledger" ...
    # PROD=GEN&FILE=FILEFLD&INDEX=FFLSET1&KEY=LSAPPS%3DGLTRANS&FIELD=FLDNAME;NOCCURS;FLDTYPE;ISGROUP;LEVEL&MAX=300
    #   data of GLTRANS fields
    # PROD=GEN&FILE=FILEIND&FIELD=INDEXNAME&KEY=LSAPPS%3DGLTRANS
    #   list of indexes for GLTRANS (GLTSET1...)
    # PROD=GEN&FILE=FILECND&FIELD=CNDNAME&KEY=LSAPPS%3DGLTRANS
    #   list of conditions for GLTRANS
    # PROD=GEN&FILE=FILEREL&INDEX=FRLSET1&KEY=LSAPPS%3DGLTRANS&FIELD=RelName;RelFile
    #   list of related fields (foreign keys) and related files (table with matching primary key)
    # PROD=GEN&FILE=FILEFLD&FIELD=ALL&KEY=LSAPPS%3DGLCHARTDTL&MAX=1
    #   list primary key of GLCHARTDTL?
    # PROD=GEN&FILE=FILEFLD&INDEX=FFLSET1&FIELD=FLDNAME;NOCCURS;FLDTYPE;ISGROUP;LEVEL;ELEMENTNAME&KEY=LSAPPS%3DGLCHARTDTL
    #   list field info for GLCHARTDTL
    # PROD=GEN&FILE=FILERELFLD&INDEX=FRFSET1&FIELD=FRFILENAME;FRFLDNAME&KEY=LSAPPS%3DGLTRANS%3DCHART-DETAIL
    #   list file related field info for GLTRANS/CHART-DETAIL
    # PROD=GEN&FILE=FILEINDFLD&FIELD=FLDNAME&KEY=LSAPPS%3DGLTRANS%3DGLTSET3
    #   list file index fields
    # PROD=GEN&FILE=FILEREL&FIELD=RELFILE&KEY=LSAPPS%3DGLTRANS%3DCHART-DETAIL
    #   returns name of table to which foreign key field relates
    # PROD=GEN&FILE=ELEMENT&KEY=LSAPPS%3DACCOUNT-DESC&FIELD=ELEMENTNAME;TYPE
    #   returns "ACCOUNT-DESC",30
    # PROD=GEN&FILE=FILEFLD&INDEX=FFLSET2&FIELD=FLDNAME;ELEMENTNAME&KEY=LSAPPS%3DCONTROL-GROUP%3DGLCONTROL
    #   returns CONTROL-GROUP,CONTROL-GROUP
    # /cgi-lawson/formdef.exe?RequestCacheID=48209650513896313351456957240951
    #   complete portal form details
    # /cgi-lawson/formdef.exe _OUT=MS&_PDL=LSAPPS&_TKN=GL40.2&_DELIM=%09
    #   complete portal form details
