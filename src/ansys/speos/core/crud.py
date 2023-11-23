"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""


class CrudStub:
    """Wraps a speos gRPC CRUD connection."""

    def __init__(self, stub):
        self._stubMngr = stub

    def create(self, request):
        """Create a new entry."""
        return self._stubMngr.Create(request)

    def read(self, request):
        """Get an existing entry."""
        return self._stubMngr.Read(request)

    def update(self, request):
        """Change an existing entry."""
        self._stubMngr.Update(request)

    def delete(self, request):
        """Remove an existing entry."""
        self._stubMngr.Delete(request)

    def list(self, request):
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
