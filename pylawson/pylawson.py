from base64 import b64encode
# noinspection PyPackageRequirements
from bs4 import BeautifulSoup
import json
from requests import Session
from requests.compat import cookielib
from urllib.parse import urljoin, urlparse


class IosError(Exception):
    """Exceptions raised from IOS connection errors."""
    def __init__(self, message: str):
        self.message = message


class Ios(object):
    """Authenticate MS-SAMLPR session for Infor Lawson cloud services."""
    def __init__(self, target_resource: str=None, ident_provider: str=None, username: str=None, password: str=None):
        self._host = None
        try:
            resources = json.load(open('pylawson.json', 'r'))
            self.username = resources.get('name')
            self._password = resources.get('word')
            self.target_resource = resources.get('target_resource')
            self._host = resources.get('host', urlparse(self.target_resource).netloc)
            self.ident_provider = resources.get('ident_provider')
        except FileNotFoundError:
            if None in (target_resource, ident_provider, username, password):
                raise IosError('Missing argument and no pylawson.json file found.')
        finally:
            if username is not None:
                self.username = username
            if password is not None:
                self._password = password
            if target_resource is not None:
                self.target_resource = target_resource
            if self._host is None:
                self._host = urlparse(target_resource).netloc
            if ident_provider is not None:
                self.ident_provider = ident_provider
        self._history = {}
        self.headers = {
            'Upgrade-Insecure-Requests': '1', 'Accept-Language': 'en-US,en',
            'Accept': 'text/html,application/xhtml+xml,application/xml,image/webp,*/*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
            'Chrome/53.0.2785.143 Safari/537.36'
        }
        self.sso_status = None
        self.sso_timeout = None
        self.session = Session()
        self._ip_cookie = cookielib.Cookie(
            version=0, name='MSISIPSelectionPersistent',
            value=b64encode(self.ident_provider.encode('utf-8')).decode('utf-8'),
            port=None, port_specified=False, domain=self._host, domain_specified=False,
            domain_initial_dot=False, path='/adfs/ls', path_specified=True, secure=True,
            expires=cookielib.timegm(cookielib.time.localtime())+2500000, discard=False,
            comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        self.session.cookies.set_cookie(self._ip_cookie)
        self.session.headers.update(self.headers)
        self._xfer_session = None
        self.productline = None

    def save_resources(self):
        """Save pylawson.json file with currently set resources."""
        if isinstance(self.username, str) and isinstance(self._password, str):
            resource = {'name': self.username, 'word': self._password}
        else:
            raise IosError('Not saved: Missing resource values.')
        if self.target_resource is not None:
            resource['target_resource'] = self.target_resource
        if self.ident_provider is not None:
            resource['ident_provider'] = self.ident_provider
        if self._host is not None:
            resource['host'] = self._host
        json.dump(resource, open('pylawson.json', 'w'))

    @property
    def history(self) -> dict:
        """Dictionary of Response objects from series of authentication step requests."""
        return self._history

    def _form(self, response) -> (str, dict):
        """Read Response text and return Form URL and Data to post."""
        soup = BeautifulSoup(response.text, 'html.parser')
        data = {}
        select = soup.find('select')
        if len(soup.find_all('select')) > 1:
            raise IosError('Unsupported number of Forms on page.')
        if select is not None and 'Provider' in select.get('name'):
            data[select] = self.ident_provider
        for element in soup.find_all('input'):
            if element.has_attr('name') and element.has_attr('value'):
                data[element['name']] = element['value']
            elif element.has_attr('name') and 'Username' in element.get('name'):
                data[element['name']] = self.username
            elif element.has_attr('name') and 'Password' in element.get('name'):
                data[element['name']] = self._password
        action = urljoin(response.url, soup.find('form').get('action'))
        return action, data

    @property
    def ping(self) -> int:
        """Return number of milliseconds remaining until login session times out."""
        soup = BeautifulSoup(self.session.get(urljoin(self.target_resource, '?_action=PING')).text, 'html.parser')
        if soup.find('sessionstatus').text == 'true':
            self.sso_status = 'Active as ' + soup.find('username').text
        else:
            self.sso_status = 'Inactive'
            return 0
        milliseconds = self.sso_timeout + int(soup.find('time_remaining').text)
        print('Time remaining: ', cookielib.datetime.timedelta(milliseconds=milliseconds).__str__()[:-5])
        return milliseconds

    def xfer_session(self, url: str=''):
        """Go to Transfer Session URL."""
        if self._xfer_session is None:
            raise IosError('Called Ios.xfer_session before session authorized.')
        if not url:
            url = self._xfer_session
        response = self.session.get(url, allow_redirects=False)
        self.sso_status = response.headers.get('SSO_STATUS', 'NoStatusHeader')
        self.sso_timeout = int(response.headers.get('SSO_TIMEOUT_REMAINING', 0))
        if response.cookies.get('C.LWSN') is None or response.status_code != 302:
            raise IosError('Unexpected response from Transfer Session URL.')
        self._xfer_session = self.session.get(urljoin(self.target_resource, '?_action=GET_XFER_SESSION')).text

    def profile(self) -> dict:
        """Set productline attribute and return dictionary of current user's profile attributes."""
        soup = BeautifulSoup(
            self.session.get(urljoin(self.target_resource, '/servlet/Profile?section=attributes')).text, 'html.parser'
        )
        profile_dict = {element.attrs['name']: element.attrs['value'] for element in soup.find_all('attr')}
        self.productline = profile_dict.get('productline')
        return profile_dict

    def logout(self):
        """Log out of Infor server and close session."""
        if self.session is not None:
            response = self.session.get(urljoin(self.target_resource, '?_action=LOGOUT'))
            self.sso_status = response.headers.get('SSO_STATUS')
            self.session.close()
        else:
            self.sso_status = None

    def auth(self, debug: bool=False):
        """Perform series of requests for SAML authentication."""

        # Initialize separate session for Identity Provider requests
        ipsession = Session()
        ipsession.headers.update(self.headers)

        # 1 - Request the target resource at service provider - status 302
        self._history[1] = self.session.get(self.target_resource, allow_redirects=False)
        if 'wa=wsignin' not in self._history[1].headers.get('Location') or self._history[1].status_code != 302:
            raise IosError('Unexpected response from initial Target Resource Request (history[1]).')

        # 2 - Discover Identity Provider - form to select IdP (unless persistent cookie) - status 200
        self._history[2] = self.session.get(self._history[1].headers['Location'], allow_redirects=False)
        if self._history[2].status_code == 200:
            url, data = self._form(self._history[2])

        # 3 - Redirect to SSO Service at IdP - status 302
            self._history[3] = self.session.post(url, allow_redirects=False, data=data)
            redirect = self._history[3].headers.get('Location')
            if self._history[3].cookies.get('MSISIPSelectionSession') is None:
                raise IosError('Unexpected response from Identity Provider Form Submission (history[3]).')
        else:
            redirect = self._history[2].headers.get('Location')
            if self._history[2].cookies.get('MSISIPSelectionSession') is None:
                raise IosError('Unexpected response from SSO Service Redirect (history[2]).')

        # 4 - Request the SSO Service at IdP - provides sign in form - status 200
        self._history[4] = ipsession.get(
                redirect, allow_redirects=False, headers={'Referer': self._history[2].url}
            )
        url, data = self._form(self._history[4])
        if 'wa=wsignin' not in url or self._history[4].status_code != 200:
            raise IosError('Unexpected response from Sign In Form Submission (history[4]).')

        # 5 - Identify the user - sets auth cookies - status 302
        self._history[5] = ipsession.post(
            url, allow_redirects=False, data=data, headers={'Referer': self._history[4].url}
        )
        if self._history[5].cookies.get('MSISAuth') is None or self._history[5].status_code != 302:
            # TODO: This error is where an old password pops up. Just returns to login page (from page 4)
            raise IosError('Unexpected response from Sign In Redirect (history[5]).')

        # 6 - Respond with XHTML form - status 200 (JS autosubmit script)
        self._history[6] = ipsession.get(
            self._history[5].headers['Location'], allow_redirects=False, headers={'Referer': self._history[5].url}
        )
        url, data = self._form(self._history[6])
        if self._history[6].cookies.get('MSISAuthenticated') is None or self._history[6].status_code != 200:
            raise IosError('Unexpected response from SSO XHTML Form (history[6]).')

        # 7 - Request Assertion Consumer Service at Service Provider - status 200 (JS autosubmit script)
        self._history[7] = self.session.post(
            url, allow_redirects=False, data=data, headers={'Referer': self._history[6].url}
        )
        url, data = self._form(self._history[7])
        if self._history[7].cookies.get('MSISSignOut') is None or self._history[7].status_code != 200:
            raise IosError('Unexpected response from Assertion Consumer Service Request (history[7]).')

        # 8 - Redirect to target resource - sets C.LWSN session cookie finally - status 302
        self._history[8] = self.session.post(
            url, allow_redirects=False, data=data, headers={'Referer': self._history[7].url}
        )
        self.sso_status = self._history[8].headers.get('SSO_STATUS', 'NoStatusHeader')  # LoginSuccessful
        self.sso_timeout = int(self._history[8].headers.get('SSO_TIMEOUT_REMAINING', 0))  # 3600000
        if self._history[8].cookies.get('C.LWSN') is None or self._history[8].status_code != 302:
            raise IosError('Unexpected response from Target Resource Redirect (history[8]).')

        # 9 - Request target resource again - status 200 - (JS redirects to LOGINCOMPLETE)
        self._history[9] = self.session.get(
            self._history[8].headers['Location'], allow_redirects=False,
            headers={'Referer': self._history[8].url}
        )
        if 'LOGINCOMPLETE' not in self._history[9].text:
            raise IosError('Unexpected response from Target Resource (history[9]).')

        # Get Transfer Session URL for session refresh later.
        self._xfer_session = self.session.get(urljoin(self.target_resource, '?_action=GET_XFER_SESSION')).text

        ipsession.close()
        if not debug:
            self._history = None

    def call(self, call_type: str, params: dict) -> BeautifulSoup:
        if not self.productline:
            _ = self.profile()
        if call_type not in ('Data', 'Transaction', 'Drill', 'Attach'):
            raise IosError('Invalid call type.')
        if call_type in ('Data', 'Drill') and params.get('PROD') is None:
            params['PROD'] = self.productline
        elif call_type == 'Transaction' and params.get('_PDL') is None:
            params['_PDL'] = self.productline
        elif call_type == 'Attach' and params.get('dataArea') is None:
            params['dataArea'] = self.productline
        if call_type in ('Data', 'Drill', 'Transaction'):
            url = urljoin(self.target_resource, '/servlet/Router/' + call_type + '/erp')
        elif call_type == 'Attach':
            url = urljoin(self.target_resource, '/lawson-ios/action/ListAttachments')
        # noinspection PyUnboundLocalVariable
        soup = BeautifulSoup(self.session.post(url, data=params).text.encode('utf-8'), 'lxml-xml')
        if soup.contents[0].name == 'ERROR':
            raise IosError('Infor error: [{}] {}'.format(soup.contents[0].attrs.get('key'), soup('MSG')[0].text))
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
