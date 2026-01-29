# Copyright (C) 2021 - 2026 ANSYS, Inc. and/or its affiliates.
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

"""Define supported transport options for the FileTransfer Tool client.

This module provides classes and enumerations to configure and manage
different transport modes (UDS, mTLS, Insecure) for the FileTransfer Tool.
"""

from dataclasses import dataclass
import enum
from pathlib import Path

from ansys.tools.common.cyberchannel import create_channel


class TransportMode(enum.Enum):
    """Enumeration of transport modes supported by the FileTransfer Tool."""

    UDS = "uds"
    MTLS = "mtls"
    INSECURE = "insecure"
    WNUA = "wnua"


@dataclass(kw_only=True)
class UDSOptions:
    """Options for UDS transport mode."""

    uds_service: str | None = None
    uds_dir: str | Path | None = None
    uds_id: str | None = None
    uds_fullpath: str | Path | None = None

    def _to_cyberchannel_kwargs(self):
        return {
            "uds_service": self.uds_service,
            "uds_dir": self.uds_dir,
            "uds_id": self.uds_id,
            "uds_fullpath": self.uds_fullpath,
        }


@dataclass(kw_only=True)
class MTLSOptions:
    """Options for mTLS transport mode."""

    certs_dir: str | Path | None = None
    host: str = "localhost"
    port: int
    allow_remote_host: bool = False

    def _to_cyberchannel_kwargs(self):
        if not self.allow_remote_host:
            if self.host not in ("localhost", "127.0.0.1"):
                raise ValueError(
                    f"Remote host '{self.host}' is not allowed when "
                    "'allow_remote_host' is set to False."
                )
        return {
            "certs_dir": self.certs_dir,
            "host": self.host,
            "port": self.port,
        }


@dataclass(kw_only=True)
class InsecureOptions:
    """Options for insecure transport mode."""

    host: str = "localhost"
    port: int
    allow_remote_host: bool = False

    def _to_cyberchannel_kwargs(self):
        if not self.allow_remote_host:
            if self.host not in ("localhost", "127.0.0.1"):
                raise ValueError(
                    f"Remote host '{self.host}' is not allowed when "
                    "'allow_remote_host' is set to False."
                )
        return {
            "host": self.host,
            "port": self.port,
        }


@dataclass(kw_only=True)
class WNUAOptions:
    """Options for Windows Named User Authentication transport mode."""

    host: str = "localhost"
    port: int

    def _to_cyberchannel_kwargs(self):
        return {
            "host": self.host,
            "port": self.port,
        }


@dataclass(kw_only=True)
class TransportOptions:
    """Transport options for the FileTransfer Tool client."""

    mode: TransportMode
    options: UDSOptions | MTLSOptions | InsecureOptions | WNUAOptions

    def __init__(
        self,
        mode: TransportMode | str = "uds",
        options: UDSOptions | MTLSOptions | InsecureOptions | WNUAOptions | None = None,
    ):
        if isinstance(mode, str):
            mode = TransportMode(mode)
        if options is None:
            if mode != TransportMode.UDS:
                raise RuntimeError("TransportOptions must be provided for modes other than UDS.")
            # The default cannot be set in the constructor signature
            # since '_get_uds_dir_default' may raise.
            options = UDSOptions()

        if mode == TransportMode.UDS:
            if not isinstance(options, UDSOptions):
                raise TypeError("For UDS transport mode, options must be of type UDSOptions.")
        elif mode == TransportMode.MTLS:
            if not isinstance(options, MTLSOptions):
                raise TypeError("For mTLS transport mode, options must be of type MTLSOptions.")
        elif mode == TransportMode.INSECURE:
            if not isinstance(options, InsecureOptions):
                raise TypeError(
                    "For Insecure transport mode, options must be of type InsecureOptions."
                )
        elif mode == TransportMode.WNUA:
            if not isinstance(options, WNUAOptions):
                raise TypeError("For WNUA transport mode, options must be of type WNUAOptions.")
        else:
            raise ValueError(f"Unsupported transport mode: {mode}")

        self.mode = mode
        self.options = options

    def _to_cyberchannel_kwargs(self):
        """Convert transport options to cyberchannel kwargs."""
        return {
            "transport_mode": self.mode.value,
            **self.options._to_cyberchannel_kwargs(),
        }

    def create_channel(self, grpc_options):
        """Create a gRPC channel based on the transport options."""
        return create_channel(**self._to_cyberchannel_kwargs(), grpc_options=grpc_options)
