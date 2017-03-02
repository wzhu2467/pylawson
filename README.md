# pylawson
This package exposes a Python API to connect to Infor Lawson IOS services.

The `pylawson.client` package contains Session objects for authenticating on the lawson server: 
`sec_api.SecApiSession` for Windows utilizes the `sec-api.dll` library which is installed with 
the Lawson Excel Add-Ins; and `ms_samlpr.SamlSession` which uses `requests` to robotically 
authenticate through the SAML login session.

Simple use:

First create a json file with connection details (each value is optional and can alternatively
be passed directly to the session instantiation):

```json
{"lawson": 
    {
        "lawson_server": "https://target.resource/sso/SSOServlet",
        "ident_server": "http://identity.provider/adfs", 
        "ident_host": "identity.provider", 
        "username": "username", 
        "password": "password" 
    }
}
```

Then write a couple of lines of code:

```python
from pylawson import Tokens
from pylawson.client import SamlSession as Ios
lawson = Ios(json_file='./pylawson.json')
response = lawson.tokens({'systemCode': 'GL'})
```

This authenticates on the server and returns Lawson's XML response in a string with the result
of a ListTokens action for the GL system.

**NOTE:** The IOS URL's and parameters are documented in Infor's *'Doc for Developers: IOS Application 
Program Interfaces--Windows'* available on the Infor Xtreme support site.