.. _ref_user_guide:

==========
User guide
==========

This section provides an overview of the PyAnsys Speos library,
explaining its key concepts.

PyAnsys Speos overview
======================

PyAnsys Speos is a Python client to communicate with the Ansys SpeosRPC Server.

The SpeosRPC Server is based on gRPC and provides APIs to interact with Speos Solver.

.. warning::

   Please be aware that the server is intended to work with a single user.

.. warning::

   The server is under development, so all Speos features are not available yet.

Why SpeosRPC Server?
====================

This allows the user to use the Speos capabilities without starting any CAD.

This offers the possibility to manage Speos capabilities with more liberty:

* Data preparation
* Running jobs
* Result post processing

gRPC usage advantages
=====================

There are several advantages of using gRPC.

* Language independency between client and server. This means that the user has a large choice of languages to write the API calls. The user does not have to write the same language as the server.
* OS independency between client and server. The client does not have to run on the same OS as the server. The SpeosRPC server is provided for Linux and Windows.
* The client and server can run on different machines.

Schema
======

The schema shows different ways to use Speos capabilities:

* via CADs / Labs / Viewers GUIs
* via SpeosRPC Server APIs

Schema Here

Speos Solver
------------

The Speos Solver represents the intelligence that is used to handle the light simulation.

SpeosRPC Server
---------------

The SpeosRPC Server allows to translate the provided gRPC API calls into features understood by the Speos Solver.
