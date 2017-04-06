pylawson
========

This package exposes a Python API to connect to Infor Lawson IOS services.

The ``pylawson.client`` package contains Session objects for authenticating on the lawson server:
``sec_api.SecApiSession`` for Windows utilizes the ``sec-api.dll`` library which is installed with
the Lawson Excel Add-Ins; and ``ms_samlpr.SamlSession`` which uses ``requests`` to robotically
authenticate through the SAML login session.

Simple, no-hands use with SAML
------------------------------

First create a json file with connection details (each value is optional and can alternatively
be passed directly to the session instantiation):

.. code-block:: python

    {"lawson":
        {
            "lawson_server": "https://target.resource/sso/SSOServlet",
            "ident_server": "http://identity.provider/adfs",
            "ident_host": "identity.provider",
            "username": "username",
            "password": "password"
        }
    }

The ``ident_host`` argument is optional and specifies the domain for a ``MSISIPSelectionPersistent`` cookie that is
created to bypass the Identity Provider selection step. If omitted, it will default to the domain of the
``ident_server``. If the persistent cookie is not recognized, ``pylawson`` expects to get a form where the first
``select`` tag will accept the ``ident_server`` value.

Then write a couple of lines of code:

.. code-block:: python

    from pylawson.client import SamlSession as Ios
    lawson = Ios(json_file='./pylawson.json')
    response = lawson.tokens({'systemCode': 'GL'})

This authenticates on the server and returns Lawson's XML response in a string with the result
of a ListTokens action for the GL system.

Simpler still with SEC-API
--------------------------

This will require the user to select the server and log in, but no special parameters are required:

.. code-block:: python

    from pylawson.client import SecApiSession as Ios
    lawson = Ios(client_display_name='Login Window Title')
    response = lawson.tokens({'systemCode': 'GL'})

More Info
---------

**NOTE:** The IOS URL's and parameters are documented in Infor's *'Doc for Developers: IOS Application
Program Interfaces--Windows'* available on the Infor Xtreme support site.
