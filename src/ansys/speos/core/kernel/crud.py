# Copyright (C) 2021 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Provides a wrapped abstraction of the gRPC proto API definition and stubs."""


class CrudStub:
    """Wraps a speos gRPC CRUD connection.

    This class is used as base class for all Speos databases interactions.
    Better use directly those inherited classes like SOPTemplateStub, SpectrumStub, ...
    """

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
    """Item of a database.

    Parameters
    ----------
    db : ansys.speos.core.kernel.crud.CrudStub
        Database to link to.
    key : str
        Key (also named guid) of the item in the database.
    """

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
