class KidShuttleBaseError(Exception):
    """Root exception for all project errors."""


class ConnectorError(KidShuttleBaseError):
    """Raised when a source connector fails to fetch data."""


class RenderError(KidShuttleBaseError):
    """Raised when markdown rendering fails."""


class UploadError(KidShuttleBaseError):
    """Raised when MinIO upload fails."""


class ManifestError(KidShuttleBaseError):
    """Raised when manifest read/write fails."""


class MissingColumnError(ConnectorError):
    """Raised when a required Excel column is missing."""


class SyncError(KidShuttleBaseError):
    """Raised when a sync run encounters a fatal error."""
