# pylawson
This module exposes a Python API to connect to Infor Lawson IOS services by connecting to the 
Infor Lawson Office Add-ins .NET library (Infor Security sec-api.dll).

Simple use:

```python
import pylawson as ios
url = '/lawson-ios/action/ListTokens?productLine=' + lawson.profile['productline'] + '&systemCode=GL'
response_xml = ''
with ios.Session() as lawson:
    lawson.login()
    lawson.get_profile()
    response_xml = lawson.get(url)
```

The IOS URL's and parameters are documented in Infor's 'Doc for Developers: IOS Application Program Interfaces--Windows'
