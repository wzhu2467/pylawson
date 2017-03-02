# Current API

object `Ios`
---
method `__init__(target_resource, ident_provider, username, password)`

method `save_resources()`

property `history()`

method `_form(response)`

property `ping()`

method `xfer_session()`

method `profile()`

method `logout()`

method `auth(debug)`

method `call(call_type, params)`

method `gl40_2(params)`

method `gl40_1(params)`

method `gl90(params)`

method `ac10_inquire(params)`

method `ac10_add(params)`


# Target API

object `Session`
---
-- implemented as either `sec_api` or `requests`

method `__init__(json_file, lawson_server, ident_server, username, password)`
-- instantiation should authenticate and acquire profile attributes + `xfer_session`

property `is_authenticated`
-- should process ping and/or return connection.IsAuthenticated

property `profile` -> dict

method `get(url)` or `post(url, data)`

method `close()`
-- should log out and close session

object `LawsonBase`
---
basic Lawson object class

object `JournalLine`
---
-- repr acct/period/desc
-- link to Journal, Account
-- get/send methods

object `Journal`
---
-- repr sys/period/desc, number of lines
-- link to JournalLines
-- get/send methods

object `InterfaceLine`
---
-- repr sys/acct/period/desc
-- link to Account
-- get/send methods

object `Account`
---
-- repr co/acct/desc
-- get/send methods

object `Activity`
---
-- repr activity/desc
-- get/send methods
