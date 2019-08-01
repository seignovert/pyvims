"""VIMS ISIS generic errors."""


class VIMSError(Exception):
    """Generic VIMS error."""


class ISISError(Exception):
    """Generic ISIS error."""


class VIMSCameraError(VIMSError):
    """Generic VIMS Camera error."""
