"""SecApiSession: IosSession using Infor Lawson Office Add-ins .NET library (Infor Security sec-api.dll)."""
from io import IOBase
from logging import getLogger
import os
from typing import Union
from urllib.parse import urlencode, urljoin
# noinspection PyPackageRequirements
from bs4 import BeautifulSoup
from pylawson import IosError, IosAuthenticationError, IosConnectionError
from pylawson.client import IosSession

# noinspection PyPackageRequirements
import clr
try:
    _ = clr.AddReference(
        os.getenv('PROGRAMFILES(x86)', r'c:\Program Files (x86)') + r'\Lawson Software\Office Add-ins\sec-api.dll'
    )
except FileNotFoundError:
    _ = clr.AddReference(
        os.getenv('PROGRAMFILES', r'c:\Program Files') + r'\Lawson Software\Office Add-ins\sec-api.dll'
    )
# noinspection PyUnresolvedReferences,PyPackageRequirements
from Security import EnvironmentManagement, Factory, LawsonHttpClient, LSConnect
# noinspection PyUnresolvedReferences,PyPackageRequirements
from System import Threading

logger = getLogger(__name__)


def authorized(func):
    """Wrapper to ensure authorization session is current before making a data call."""
    def wrapper(*args):
        instance = args[0]
        if not instance.server or not instance.connection.IsAuthenticated():
            instance.login(login_string='Log in again to continue.')
        try:
            assert instance.profile.productline is not None
        except (AttributeError, AssertionError):
            instance.login(login_string='Log in again to continue.')
        return func(*args)

    return wrapper


class SecApiSession(IosSession):
    """
    Subclasses pylawson.IosSession using Infor Lawson Office Add-ins .NET library (Infor Security sec-api.dll)

    The Infor sec-api library will pop up a login window; as such, this class does not accept username/password.
    """
    def __init__(self, json_file: Union[str, IOBase] = None, lawson_server: str = None, ident_server: str = None):
        super().__init__(json_file=json_file, lawson_server=lawson_server, ident_server=ident_server,
                         username=None, password=None)
        # The sec-api .NET library crashes if it doesn't detect a Single Apartment State environment.
        thread = Threading.Thread.CurrentThread
        if not thread.TrySetApartmentState(Threading.ApartmentState.STA):
            msg = 'CLR failed to set .NET Single Apartment State environment.'
            logger.error(msg=msg)
            raise IosError(msg)

        # The Security Factory class has the function to instantiate the Authenticator Interface,
        # which in turn has the Login function which returns our Connection Interface.
        factory = Factory.ClientCOMSecurityFactory()
        factory.Path = os.getcwd()
        self.authenticator = factory.GetClientSecurityAuthenticator()
        if factory.Error:
            msg = 'SEC-API error: {}'.format(factory.Error)
            logger.error(msg)
            raise IosConnectionError(msg)

        # The balance of our methods are found on the Connection Interface.
        self.connection = None
        self.server = None
        logger.debug('Basic SecApiSession instantiation completed.')

        # Run login, which populates self.connection, self._xfer_url, self.server, and self._profile
        self.login(clientDisplayName='Python Infor Login')

    def __bool__(self) -> bool:
        """Status of connection."""
        return self.connection.IsAuthenticated()

    def _get(self, url: str) -> str:
        """Send GET call to server, return response data. (Not wrapped, for initial profile call."""
        url = urljoin(self.server, url)
        response = self.connection.SendData(url)
        return response.ResponseData

    @authorized
    def get(self, url: str) -> str:
        """Send GET call to server, return response data."""
        return self._get(url=url)

    @authorized
    def post(self, url, data):
        """Mimic POST call to server with GET, return response data."""
        s = urlencode(data) if isinstance(data, dict) else data
        return self.get('?{}'.format(s))

    def close(self):
        """Logout and remove connection."""
        self.connection.Logout()
        self.connection = None
        logger.info(msg='Closed session.')

    # noinspection PyPep8Naming
    def login(self, clientDisplayName: str):
        """Pop up Login window for user to log in to Lawson.

        Creates the IConnectionHandler object, then populates the _xfer_url, server, and _profile variables.

        :param clientDisplayName: .NET window title
        :raise IosAuthenticationError: if login window returns without valid session
        """
        self.connection = self.authenticator.DoActiveClientLogin(clientDisplayName)
        if self:
            self._xfer_url = self.connection.GetTransferSessionToken()  # Transfer token for session persistence.
            self.server = self.connection.GetConnectedServerUrl()  # Lawson server which we have logged in to.
            # Profile Attributes for the logged-in user.
            soup = BeautifulSoup(self._get('/servlet/Profile?section=attributes'), 'html.parser')
            self._profile.__dict__ = {element.attrs['name'].lower(): element.attrs['value'] for element in
                                      soup.find_all('attr')}
            logger.debug('Populated profile.')

        else:
            msg = 'Authentication failed after login window returned.'
            logger.error(msg=msg)
            raise IosAuthenticationError(msg)
