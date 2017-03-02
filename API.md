# Current API

object `Ios`
---
method `call(call_type, params)`

method `gl40_2(params)`

method `gl40_1(params)`

method `gl90(params)`

method `ac10_inquire(params)`

method `ac10_add(params)`


# Target API

object `IosSession`
---
-- implemented as either `sec_api` or `ms_samlpr`

method `__init__(json_file, lawson_server, ident_server, username, password)`
-- on instantiation authenticate and acquire profile attributes + `xfer_session`

property `is_authenticated`
-- process ping and/or return connection.IsAuthenticated

property `profile`
-- `.__dict__` to contain Lawson user profile attributes (most notably `productline`)

method `get(url)` or `post(url, data)`

method `close()`
-- log out and close session

object `LawsonBase`
---
basic Lawson object class

object `JournalLine`
---
-- repr acct/period/desc
-- link to Journal, Account
-- query/upload methods

object `Journal`
---
-- repr sys/period/desc, number of lines
-- link to JournalLines
-- query/upload methods

object `InterfaceLine`
---
-- repr sys/acct/period/desc
-- link to Account
-- query/upload methods

object `Account`
---
-- repr co/acct/desc
-- query/upload methods

object `Activity`
---
-- repr activity/desc
-- query/upload methods
