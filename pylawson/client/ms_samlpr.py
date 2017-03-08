from base64 import b64encode
from io import IOBase
from logging import getLogger
from typing import Union
# noinspection PyPackageRequirements
from bs4 import BeautifulSoup
from requests import Session
from requests.compat import cookielib
from urllib.parse import urljoin, urlparse
from pylawson import IosAuthenticationError, IosConnectionError
from pylawson.client import IosSession

logger = getLogger(__name__)


class SamlSession(IosSession):
    def __init__(self, json_file: Union[str, IOBase] = None, lawson_server: str = None, ident_server: str = None,
                 username: str = None, password: str = None):
        super().__init__(json_file=json_file, lawson_server=lawson_server, ident_server=ident_server,
                         username=username, password=password)
        self._sso = None
        headers = {
            'Upgrade-Insecure-Requests': '1', 'Accept-Language': 'en-US,en',
            'Accept': 'text/html,application/xhtml+xml,application/xml,image/webp,*/*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                          'Chrome/53.0.2785.143 Safari/537.36'
        }
        ip_host = self._params['ident_host'] or urlparse(self._params['lawson_server']).netloc
        ip_cookie = cookielib.Cookie(
            version=0, name='MSISIPSelectionPersistent',
            value=b64encode(self._params['ident_server'].encode('utf-8')).decode('utf-8'),
            port=None, port_specified=False, domain=ip_host, domain_specified=False,
            domain_initial_dot=False, path='/adfs/ls', path_specified=True, secure=True,
            expires=cookielib.timegm(cookielib.time.localtime()) + 2500000, discard=False,
            comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        self.session = Session()
        self.session.cookies.set_cookie(ip_cookie)
        self.session.headers.update(headers)
        logger.debug('Basic SamlSession instantiation completed.')
        self._auth()

    def __bool__(self):
        soup = BeautifulSoup(self.get('?_action=PING'), 'html.parser')
        if soup.find('sessionstatus').text == 'true':
            status = 'Active as {}, '.format(soup.find('username').text)
            milliseconds = self._sso[1] + int(soup.find('time_remaining').text)
            status += 'time remaining: {}'.format(
                cookielib.datetime.timedelta(milliseconds=milliseconds).__str__()[:-5])
            logger.debug(msg=status)
            return True

        return False

    def get(self, url: str) -> str:
        url = urljoin(self._params['lawson_server'], url)
        return self.session.get(url=url).text

    def post(self, url: str, data: dict) -> str:
        url = urljoin(self._params['lawson_server'], url)
        return self.session.post(url=url, data=data).text

    def close(self):
        if self:
            self.get(url='?_action=LOGOUT')
            self.session.close()
        logger.info(msg='Closed session.')

    def _auth(self):
        """Perform series of requests for SAML authentication."""

        # 1 - Request the target resource at service provider - status 302
        response = self.session.get(url=self._params['lawson_server'], allow_redirects=False)
        logger.debug(msg='Auth #1 - request target resource')
        if 'wa=wsignin' not in response.headers.get('Location', '') or response.status_code != 302:
            msg = 'Unexpected response from initial Target Resource Request.'
            logger.error(msg=msg)
            raise IosConnectionError(msg)

        # 2 - Discover Identity Provider - form to select IdP (unless persistent cookie) - status 200
        id_response = self.session.get(url=response.headers['Location'], allow_redirects=False)
        logger.debug(msg='Auth #2 - discover identity provider')
        if id_response.status_code == 200:
            url, data = self._form(id_response)

            # 3 - Redirect to SSO Service at IdP - status 302
            response = self.session.post(url, allow_redirects=False, data=data)
            logger.debug(msg='Auth #3 - redirect to SSO service')
            redirect = response.headers.get('Location')
            if response.cookies.get('MSISIPSelectionSession') is None:
                msg = 'Unexpected response from Identity Provider Form Submission.'
                logger.error(msg=msg)
                raise IosConnectionError(msg)
        else:
            redirect = id_response.headers.get('Location')
            if id_response.cookies.get('MSISIPSelectionSession') is None:
                msg = 'Unexpected response from SSO Service Redirect.'
                logger.error(msg=msg)
                raise IosConnectionError(msg)

        # 4 - Request the SSO Service at IdP - provides sign in form - status 200
        response = self.session.get(redirect, allow_redirects=False, headers={'Referer': id_response.url})
        logger.debug(msg='Auth #4 - request SSO service (sign in form)')
        url, data = self._form(response)
        if 'wa=wsignin' not in url or response.status_code != 200:
            msg = 'Unexpected response from Sign In Form Submission.'
            logger.error(msg=msg)
            raise IosConnectionError(msg)

        # 5 - Identify the user - sets auth cookies - status 302
        response = self.session.post(url, allow_redirects=False, data=data, headers={'Referer': response.url})
        logger.debug(msg='Auth #5 - identify the user')
        if response.cookies.get('MSISAuth') is None or response.status_code != 302:
            msg = 'Invalid username or password. (Is password expired?)'
            logger.error(msg=msg)
            raise IosAuthenticationError(msg)

        # 6 - Respond with XHTML form - status 200 (JS autosubmit script)
        response = self.session.get(
            response.headers['Location'], allow_redirects=False, headers={'Referer': response.url}
        )
        logger.debug(msg='Auth #6 - XHTML form')
        url, data = self._form(response)
        if response.cookies.get('MSISAuthenticated') is None or response.status_code != 200:
            msg = 'Unexpected response from SSO XHTML Form.'
            logger.error(msg=msg)
            raise IosConnectionError(msg)

        # 7 - Request Assertion Consumer Service at Service Provider - status 200 (JS autosubmit script)
        response = self.session.post(url, allow_redirects=False, data=data, headers={'Referer': response.url})
        logger.debug(msg='Auth #7 - request assertion consumer service')
        url, data = self._form(response)
        if response.cookies.get('MSISSignOut') is None or response.status_code != 200:
            msg = 'Unexpected response from Assertion Consumer Service Request.'
            logger.error(msg=msg)
            raise IosConnectionError(msg)

        # 8 - Redirect to target resource - sets C.LWSN session cookie finally - status 302
        response = self.session.post(url, allow_redirects=False, data=data, headers={'Referer': response.url})
        logger.debug(msg='Auth #8 - redirect to target resource')
        self._sso = (
            response.headers.get('SSO_STATUS', 'NoStatusHeader'),  # LoginSuccessful
            int(response.headers.get('SSO_TIMEOUT_REMAINING', 0))  # 3600000
        )
        logger.info('SSO Status: {}, Timeout: {} '.format(self._sso[0], self._sso[1]))
        if response.cookies.get('C.LWSN') is None or response.status_code != 302:
            msg = 'Unexpected response from Target Resource Redirect.'
            logger.error(msg=msg)
            raise IosConnectionError(msg)

        # 9 - Request target resource again - status 200 - (JS redirects to LOGINCOMPLETE)
        response = self.session.get(
            response.headers['Location'], allow_redirects=False,
            headers={'Referer': response.url}
        )
        logger.debug(msg='Auth #9 - request target resource again')
        if 'LOGINCOMPLETE' not in response.text:
            msg = 'Unexpected response from Target Resource.'
            logger.error(msg=msg)
            raise IosConnectionError(msg)

        # Get Transfer Session URL for session refresh later.
        self._xfer_url = self.session.get(urljoin(self._params['lawson_server'], '?_action=GET_XFER_SESSION')).text
        logger.debug(msg='Auth complete; XFER_SESSION response: {}.'.format(self._xfer_url))

        # Get Profile attributes
        soup = BeautifulSoup(self.get('/servlet/Profile?section=attributes'), 'html.parser')
        self._profile.__dict__ = {element.attrs['name'].lower(): element.attrs['value'] for element in
                                  soup.find_all('attr')}
        logger.debug('Populated profile.')

    def _form(self, response) -> (str, dict):
        """Read Response text and return Form URL and Data to post."""
        soup = BeautifulSoup(response.text, 'html.parser')
        data = {}
        select = soup.find('select')
        if len(soup.find_all('form')) != 1:
            msg = 'Unsupported number of Forms on page [{}].'.format(response.url)
            logger.error(msg=msg)
            raise IosConnectionError(msg)
        if select is not None and 'Provider' in select.get('name'):
            data[select] = self._params['ident_server']
        for element in soup.find_all('input'):
            if element.has_attr('name') and element.has_attr('value'):
                data[element['name']] = element['value']
            elif element.has_attr('name') and 'Username' in element.get('name'):
                data[element['name']] = self._params['username']
            elif element.has_attr('name') and 'Password' in element.get('name'):
                data[element['name']] = self._params['password']
        action = urljoin(response.url, soup.find('form').get('action'))
        return action, data
