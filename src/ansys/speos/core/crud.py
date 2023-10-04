"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""


class Database:
    """
    Wraps a speos gRPC CRUD connection.
    """

    def __init__(self, stub):
        self._stubMngr = stub

    """Create a new entry."""

    def Create(self, request):
        return self._stubMngr.Create(request)

    """Get an existing entry."""

    def Read(self, request):
        return self._stubMngr.Read(request)

    """Change an existing entry."""

    def Update(self, request):
        self._stubMngr.Update(request)

    """Remove an existing entry."""

    def Delete(self, request):
        self._stubMngr.Delete(request)

    """List existing entries."""

    def List(self):
        return self._stubMngr.List()


class DatabaseItem:
    def __init__(self, db: Database, key: str):
        self._database = db
        self._key = key

    def database(self):
        """The database."""
        return self._database

    def key(self) -> str:
        """The guid in database."""
        return self._key

    def send_read(self):
        return self._database.Read(self._key)

    def send_update(self, data):
        self._database.Update(self._key, data)

    def send_delete(self):
        self._database.Delete(self._key)
        self._key = ""
        self._database = None
