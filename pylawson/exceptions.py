class IosError(OSError):
    """An ambiguous exception occurred during this operation."""


class IosAuthenticationError(IosError, ConnectionRefusedError):
    """Authentication error while connecting to IOS; check username and password."""


class IosConnectionError(IosError, ConnectionError):
    """Exception occurred during IOS connection process."""


class IosDataError(IosError, ValueError):
    """Received an error response from the IOS server."""
