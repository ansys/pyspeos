"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""


class CrudStub:
    """Wraps a speos gRPC CRUD connection."""

    def __init__(self, stub):
        self._stubMngr = stub

    def Create(self, request):
        """Create a new entry."""
        return self._stubMngr.Create(request)

    def Read(self, request):
        """Get an existing entry."""
        return self._stubMngr.Read(request)

    def Update(self, request):
        """Change an existing entry."""
        self._stubMngr.Update(request)

    def Delete(self, request):
        """Remove an existing entry."""
        self._stubMngr.Delete(request)

    def List(self, request):
        """List existing entries."""
        return self._stubMngr.List(request)


class CrudItem:
    def __init__(self, db: CrudStub, key: str):
        self._stub = db
        self._key = key

    @property
    def stub(self) -> CrudStub:
        """The database."""
        return self._stub

    @property
    def key(self) -> str:
        """The guid in database."""
        return self._key
