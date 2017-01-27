# pylawson
This module exposes a Python API to connect to Infor Lawson IOS services by authenticating on the
Lawson server in a requests session, following the same pattern as the Lawson Excel Add-Ins (or the
pylawson.sec_api subpackage).

Simple use:

```python
from pylawson import Ios
lawson = Ios(target_resource='https://cloud.infor.com/sso/SSOServlet',
             ident_provider='http://your.co/adfs/services/trust',
             username='username',
             password='password')
lawson.save_resources()  # Creates pylawson.json file with credentials
lawson.auth()
profile = lawson.profile()
response_soup = lawson.call(call_type='Tokens', params={'systemCode': 'GL'})
```

This authenticates on the server and leaves a `BeautifulSoup` object in `response_soup` with the result
of a ListTokens action for the GL system. The `save_resources` method serializes your credentials so
that future instantiations can be accomplished with simply `lawson = Ios()`.



# pylawson.sec_api

This module exposes a Python API to connect to Infor Lawson IOS services by connecting to the 
Infor Lawson Office Add-ins .NET library (Infor Security sec-api.dll).

Simple use:

```python
import pylawson.sec_api as ios
response_xml = ''
with ios.Session() as lawson:
    lawson.login()
    lawson.get_profile()
    url = '/lawson-ios/action/ListTokens?productLine=' + lawson.profile['productline'] + '&systemCode=GL'
    response_xml = lawson.get(url)
```

This will pop up a login window allowing you to authenticate manually, then leaves an xml string in
`response_xml`.

**NOTE:** *Expect future updates to bring the sec_api API in line with the pylawson API.*

The IOS URL's and parameters are documented in Infor's **'Doc for Developers: IOS Application Program Interfaces--Windows'**
available on the Infor Xtreme support site.