.. _ref_user_guide:

========
Overview
========

This section provides an overview of the PySpeos library,
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

* via CADs / Labs / Viewers GUI
* via SpeosRPC Server APIs

.. mermaid::
   :caption: How to use Speos capabilities.
   :alt: How to use Speos capabilities.
   :align: center

   %%{init: {'theme':'neutral'}}%%

   flowchart LR

    SpeosSolver["Speos Solver"]
    SpeosRPCServer["SpeosRPC Server"]
    StandardUsers["CADs / Labs / Viewers"]
    StandardUsers --> |uses|SpeosSolver
    SpeosRPCServer --> |uses|SpeosSolver
    User --> |calls APIs from|SpeosRPCServer
    User --> |uses UI|StandardUsers


Speos Solver
------------

The Speos Solver represents the intelligence that is used to handle the light simulation.

SpeosRPC Server
---------------

The SpeosRPC Server allows to translate the provided gRPC API calls into features understood by the Speos Solver.

PySpeos layering
================

PySpeos is composed of several code layers, each of them having a different level of complexity and range of capabilities:

* core
* workflow
* kernel

Examples of usage for each layer are available in the :ref:`Examples section <ref_examples>`.

We recommend all new users to avoid using kernel layer at a first usage.

Core
----

The Core layer is the entry point of PySpeos.

It is designed to be representative of a classic Speos UI usage.

For instance, users will be able to create a project (from scratch or from SPEOS file), add/modify/delete sources, sensors, simulations, materials, geometries, and compute simulations.

Workflow
--------

The Workflow layer offers a list of user workflows combining several actions into simple usage.

For instance, users will be able to access a workflow that combines several Speos files into a single project. Another workflow allows users to display a simulation result (on windows environment only).

Kernel
------

The Kernel layer offers more flexibility and capabilities than Core and Workflow.

It is designed to be a low level wrapper, and is close to the Speos gRPC APIs.

With the Kernel layer, users need to understand the notion about Template and Instances. Refer to the SpeosRPC server documentation on the `Developer portal, Speos section <https://developer.ansys.com/docs/speos>`_ to get a full understanding.

.. warning::
    The Kernel layer is recommended for experienced users only.