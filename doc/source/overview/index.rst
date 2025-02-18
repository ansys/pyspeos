.. _ref_user_guide:

========
Overview
========

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

We recommend all new users to avoid using kernel layer at a first usage.

Core
----

It is the entry point of PySpeos.

It is designed to be representative of a classic Speos UI usage.

As an example, user will be able to create a project (from scratch or from SPEOS file), add/modify/delete sources, sensors, simulations, materials, geometries.

Workflow
--------

This layer is meant to gather user workflows.

As an example, user can access a workflow to combine several SPEOS files into a single project.

The aim of this layer is to provide workflow that combines several actions into a simple usage.

Kernel
------

This layer is the one that offers more flexibility and capabilities.

This is also the one that is closer to the Speos gRPC APIs. It can be seen as a low level wrapper.

For example it is important to understand the notion about Template and Instances, that can be found in the SpeosRPC server documentation available on the `Developer portal, Speos section <https://developer.ansys.com/docs/speos>`_.

.. warning::
    Kernel layer is recommended for experienced users only.