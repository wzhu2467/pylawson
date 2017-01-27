#! python3

"""
pylawson
~~~~~~~~

This module exposes a Python API to connect to Infor Lawson IOS services by connecting to
the Infor Lawson Office Add-ins .NET library (Infor Security sec-api.dll).
"""

import os
from urllib.parse import urlencode

import clr
from lxml import etree

try:
    _secapi = clr.AddReference(
        os.getenv('PROGRAMFILES(x86)', r'c:\Program Files (x86)') + r'\Lawson Software\Office Add-ins\sec-api.dll'
    )
except FileNotFoundError:
    _secapi = clr.AddReference(
        os.getenv('PROGRAMFILES', r'c:\Program Files') + r'\Lawson Software\Office Add-ins\sec-api.dll'
    )
from Security import EnvironmentManagement, Factory, LawsonHttpClient, LSConnect
from System import Threading


def authorized(func):
    def wrapper(*args):
        instance = args[0]
        if not instance.server or not instance.connection.IsAuthenticated():
            instance.login()
        if instance.profile['productline'] is None:
            instance.profile()
        return func(*args)

    return wrapper


class Session(object):
    def __init__(self, path=None):

        #: The sec-api .NET library crashes if it doesn't detect a Single Apartment State environment.
        thread = Threading.Thread.CurrentThread
        assert thread.TrySetApartmentState(Threading.ApartmentState.STA) == True

        #: The Security Factory class has the function to instantiate the Authenticator Interface,
        #: which in turn has the Login function which returns our Connection Interface.
        self.factory = Factory.ClientCOMSecurityFactory()
        self.factory.Path = path if path is not None else os.getcwd()
        self.authenticator = self.factory.GetClientSecurityAuthenticator()
        assert self.factory.Error == ''

        #: The balance of our methods are found on the Connection Interface.
        self.connection = None

        #: Dictionary of Profile Attributes for the logged-in user.
        self.profile = {}
        self.profile['productline'] = None

        #: Transfer token for session persistence.
        self.xfer_token = None

        #: Lawson server which we have logged in to.
        self.server = None

    def close(self):
        self.connection.Logout()
        self.connection = None

    def login(self, login_string='Python Infor Login'):
        """Pop up Login window for user to log in to Lawson."""
        self.connection = self.authenticator.DoActiveClientLogin(login_string)
        if self.connection.IsAuthenticated():
            self.xfer_token = self.connection.GetTransferSessionToken()
            self.server = self.connection.GetConnectedServerUrl()
        else:
            self.close()

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, *args):
        self.close()

    @authorized
    def get(self, url):
        """Send GET call to server, return response data."""
        response = self.connection.SendData(self.server + url)
        return response.ResponseData

    @authorized
    def post(self, url, data):
        """Mimic POST call to server with GET, return response data."""
        s = urlencode(data) if isinstance(data, dict) else data
        response = self.connection.SendData(self.server + url + '?' + s)
        return response.ResponseData

    def ping(self):
        """Call the SSO ping program and return the session status."""
        response = self.connection.SendData(self.server + '/sso/SSOServlet?_action=PING')
        # response.ResponseData == str('<?xml ...><SSO><SESSIONSTATUS><USERNAME><LANGUAGE><TIME_REMAINING></SSO>')
        try:
            doc = etree.fromstring(response.ResponseData.encode('utf-8'))
            if doc.tag != 'ERROR':
                if doc.xpath('/SSO/SESSIONSTATUS')[0].text == 'true':
                    return True
        except etree.XMLSyntaxError:
            pass
        return False

    def get_profile(self):
        """Get Profile attributes (especially Product Line, required for data and transaction calls)."""
        response = self.connection.SendData(self.server + '/servlet/Profile?section=attributes')
        doc = etree.fromstring(response.ResponseData.encode('utf-8'))
        if doc.tag == 'PROFILE':
            for elem in doc.xpath('//ATTR'):
                self.profile[elem.attrib['name']] = elem.attrib['value']
