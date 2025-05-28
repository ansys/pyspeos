.. _ref_release_notes:

Release notes
#############

This document contains the release notes for the PySpeos project.

.. vale off

.. towncrier release notes start

`0.6.0.rc0 <https://github.com/ansys/pyspeos/releases/tag/v0.6.0.rc0>`_ - May 28, 2025
======================================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - enhance the project preview: luminaire, surface, rayfile
          - `#561 <https://github.com/ansys/pyspeos/pull/561>`_

        * - lightexpert
          - `#592 <https://github.com/ansys/pyspeos/pull/592>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - bump ansys-api-speos from 0.14.2 to 0.15.2
          - `#589 <https://github.com/ansys/pyspeos/pull/589>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - add message size to nighly ci
          - `#600 <https://github.com/ansys/pyspeos/pull/600>`_

        * - coding error, switch to correct order
          - `#601 <https://github.com/ansys/pyspeos/pull/601>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - update CHANGELOG for v0.5.0
          - `#597 <https://github.com/ansys/pyspeos/pull/597>`_

        * - bump dev version into v0.6.dev0
          - `#598 <https://github.com/ansys/pyspeos/pull/598>`_


`0.5.0 <https://github.com/ansys/pyspeos/releases/tag/v0.5.0>`_ - May 26, 2025
==============================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - geopath property
          - `#551 <https://github.com/ansys/pyspeos/pull/551>`_

        * - bsdf
          - `#581 <https://github.com/ansys/pyspeos/pull/581>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - update protobuf requirement from <6,>=3.20 to >=3.20,<7 in the grpc-deps group
          - `#500 <https://github.com/ansys/pyspeos/pull/500>`_

        * - update pyvista requirement from <0.45,>=0.40.0 to >=0.40.0,<0.46
          - `#562 <https://github.com/ansys/pyspeos/pull/562>`_

        * - update pyvista[jupyter] requirement from <0.45,>=0.43 to >=0.43,<0.46
          - `#563 <https://github.com/ansys/pyspeos/pull/563>`_

        * - bump notebook from 7.3.3 to 7.4.1
          - `#566 <https://github.com/ansys/pyspeos/pull/566>`_

        * - bump the doc-deps group across 1 directory with 2 updates
          - `#571 <https://github.com/ansys/pyspeos/pull/571>`_

        * - bump notebook from 7.4.1 to 7.4.2 in the jupyter-deps group
          - `#584 <https://github.com/ansys/pyspeos/pull/584>`_

        * - bump the doc-deps group across 1 directory with 3 updates
          - `#587 <https://github.com/ansys/pyspeos/pull/587>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Update ``CONTRIBUTORS.md`` with the latest contributors
          - `#568 <https://github.com/ansys/pyspeos/pull/568>`_

        * - improve project example
          - `#572 <https://github.com/ansys/pyspeos/pull/572>`_

        * - Adjust prism example to new style
          - `#576 <https://github.com/ansys/pyspeos/pull/576>`_

        * - adjust part.py example to match new style
          - `#580 <https://github.com/ansys/pyspeos/pull/580>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Integration direction display and adjust docstrings
          - `#570 <https://github.com/ansys/pyspeos/pull/570>`_

        * - unittest update based on bug 1229712
          - `#579 <https://github.com/ansys/pyspeos/pull/579>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - pre-commit autoupdate
          - `#552 <https://github.com/ansys/pyspeos/pull/552>`_, `#578 <https://github.com/ansys/pyspeos/pull/578>`_, `#585 <https://github.com/ansys/pyspeos/pull/585>`_, `#591 <https://github.com/ansys/pyspeos/pull/591>`_

        * - update CHANGELOG for v0.4.0
          - `#558 <https://github.com/ansys/pyspeos/pull/558>`_

        * - bump dev version
          - `#559 <https://github.com/ansys/pyspeos/pull/559>`_

        * - bump ansys/actions from 9.0.2 to 9.0.6 in the actions group
          - `#560 <https://github.com/ansys/pyspeos/pull/560>`_

        * - bump the actions group with 2 updates
          - `#567 <https://github.com/ansys/pyspeos/pull/567>`_

        * - bump ansys action version with quarto fix
          - `#573 <https://github.com/ansys/pyspeos/pull/573>`_

        * - update dependabot configuration
          - `#574 <https://github.com/ansys/pyspeos/pull/574>`_

        * - update code owners
          - `#577 <https://github.com/ansys/pyspeos/pull/577>`_

        * - bump ansys/actions from 9.0.7 to 9.0.9
          - `#582 <https://github.com/ansys/pyspeos/pull/582>`_

        * - bump codecov/codecov-action from 5.4.2 to 5.4.3
          - `#590 <https://github.com/ansys/pyspeos/pull/590>`_

        * - bump ansys/actions from 9.0.9 to 9.0.11
          - `#596 <https://github.com/ansys/pyspeos/pull/596>`_


  .. tab-item:: Miscellaneous

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - improve type hints
          - `#564 <https://github.com/ansys/pyspeos/pull/564>`_


`0.4.0 <https://github.com/ansys/pyspeos/releases/tag/v0.4.0>`_ - April 17, 2025
================================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Feat/add local launcher
          - `#454 <https://github.com/ansys/pyspeos/pull/454>`_

        * - add screenshot in pyvista related methods
          - `#521 <https://github.com/ansys/pyspeos/pull/521>`_

        * - enhance the project preview: irrad, rad, camera sensor features
          - `#528 <https://github.com/ansys/pyspeos/pull/528>`_

        * - switch to ansys tools and decouple requirements
          - `#532 <https://github.com/ansys/pyspeos/pull/532>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - bump ansys-sphinx-theme from 1.3.3 to 1.4.2 in the doc-deps group
          - `#524 <https://github.com/ansys/pyspeos/pull/524>`_

        * - bump pytest-cov from 6.0.0 to 6.1.0
          - `#533 <https://github.com/ansys/pyspeos/pull/533>`_

        * - bump pytest-cov from 6.1.0 to 6.1.1
          - `#542 <https://github.com/ansys/pyspeos/pull/542>`_

        * - bump psutil from 6.1.1 to 7.0.0
          - `#555 <https://github.com/ansys/pyspeos/pull/555>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Update example combine-speos.py
          - `#499 <https://github.com/ansys/pyspeos/pull/499>`_

        * - open-results adjustments
          - `#538 <https://github.com/ansys/pyspeos/pull/538>`_

        * - adjust source example
          - `#543 <https://github.com/ansys/pyspeos/pull/543>`_

        * - adjust simulation example
          - `#545 <https://github.com/ansys/pyspeos/pull/545>`_

        * - remote instance
          - `#553 <https://github.com/ansys/pyspeos/pull/553>`_

        * - adjust sensor.py example
          - `#554 <https://github.com/ansys/pyspeos/pull/554>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - issue with nightly pipeline
          - `#534 <https://github.com/ansys/pyspeos/pull/534>`_

        * - Graphs not showing with Ansys visualizer
          - `#537 <https://github.com/ansys/pyspeos/pull/537>`_

        * - improve examples and tests due to more errors raised by the new SpeosRPC server
          - `#546 <https://github.com/ansys/pyspeos/pull/546>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - remove code-style job to use precommit.ci
          - `#523 <https://github.com/ansys/pyspeos/pull/523>`_

        * - update CHANGELOG for v0.3.0
          - `#525 <https://github.com/ansys/pyspeos/pull/525>`_

        * - bump dev version into v0.4.dev0
          - `#526 <https://github.com/ansys/pyspeos/pull/526>`_

        * - pre-commit autoupdate
          - `#529 <https://github.com/ansys/pyspeos/pull/529>`_, `#541 <https://github.com/ansys/pyspeos/pull/541>`_

        * - bump ansys/actions from 8 to 9 in the actions group
          - `#544 <https://github.com/ansys/pyspeos/pull/544>`_

        * - Rename CONTRUBUTORS.md to CONTRIBUTORS.md
          - `#548 <https://github.com/ansys/pyspeos/pull/548>`_

        * - remove strong upper bound on build dep
          - `#549 <https://github.com/ansys/pyspeos/pull/549>`_

        * - pin actions version with full commit hash
          - `#557 <https://github.com/ansys/pyspeos/pull/557>`_


`0.3.0 <https://github.com/ansys/pyspeos/releases/tag/v0.3.0>`_ - March 28, 2025
================================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - provide a way for the user to limit number of threads
          - `#508 <https://github.com/ansys/pyspeos/pull/508>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - bump pytest from 8.3.4 to 8.3.5
          - `#484 <https://github.com/ansys/pyspeos/pull/484>`_

        * - bump the doc-deps group across 1 directory with 4 updates
          - `#509 <https://github.com/ansys/pyspeos/pull/509>`_

        * - bump notebook from 7.3.2 to 7.3.3
          - `#510 <https://github.com/ansys/pyspeos/pull/510>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - fix 404 page when download example as python script
          - `#514 <https://github.com/ansys/pyspeos/pull/514>`_

        * - add example assets button
          - `#518 <https://github.com/ansys/pyspeos/pull/518>`_

        * - fix path to download assets
          - `#522 <https://github.com/ansys/pyspeos/pull/522>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - core layer loading a camera sensor
          - `#503 <https://github.com/ansys/pyspeos/pull/503>`_

        * - doc: Adjust server launch command
          - `#505 <https://github.com/ansys/pyspeos/pull/505>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - update CHANGELOG for v0.2.0
          - `#490 <https://github.com/ansys/pyspeos/pull/490>`_

        * - update CHANGELOG for v0.2.1
          - `#492 <https://github.com/ansys/pyspeos/pull/492>`_


  .. tab-item:: Miscellaneous

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - remove ruff E ignores
          - `#495 <https://github.com/ansys/pyspeos/pull/495>`_

        * - remove ruff ignores F
          - `#506 <https://github.com/ansys/pyspeos/pull/506>`_

        * - ruff n
          - `#507 <https://github.com/ansys/pyspeos/pull/507>`_

        * - ruff TD002, TD003
          - `#512 <https://github.com/ansys/pyspeos/pull/512>`_


`0.2.1 <https://github.com/ansys/pyspeos/releases/tag/v0.2.1>`_ - March 06, 2025
================================================================================

.. tab-set::


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - add mandatory token to release-github
          - `#491 <https://github.com/ansys/pyspeos/pull/491>`_


`0.2.0 <https://github.com/ansys/pyspeos/releases/tag/v0.2.0>`_ - March 06, 2025
================================================================================

.. tab-set::


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - documentation review changes
          - `#483 <https://github.com/ansys/pyspeos/pull/483>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - add missing notebook dependency
          - `#488 <https://github.com/ansys/pyspeos/pull/488>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - add project required info
          - `#470 <https://github.com/ansys/pyspeos/pull/470>`_

        * - update CHANGELOG for v0.1.1
          - `#473 <https://github.com/ansys/pyspeos/pull/473>`_

        * - update organization name
          - `#486 <https://github.com/ansys/pyspeos/pull/486>`_


  .. tab-item:: Miscellaneous

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - remove ignores for PTH
          - `#474 <https://github.com/ansys/pyspeos/pull/474>`_

        * - Remove ruff ignore for "D", pydocstyle
          - `#482 <https://github.com/ansys/pyspeos/pull/482>`_


`0.1.1 <https://github.com/ansys/pyspeos/releases/tag/v0.1.1>`_ - 2025-02-25
============================================================================

Maintenance
^^^^^^^^^^^

- update CHANGELOG for v0.1.0 `#471 <https://github.com/ansys/pyspeos/pull/471>`_
- bump dev version into v0.2.dev0 `#472 <https://github.com/ansys/pyspeos/pull/472>`_

`0.1.0 <https://github.com/ansys/pyspeos/releases/tag/v0.1.0>`_ - 2025-02-24
============================================================================

Dependencies
^^^^^^^^^^^^

- bump the doc-deps group across 1 directory with 4 updates `#452 <https://github.com/ansys/pyspeos/pull/452>`_


Documentation
^^^^^^^^^^^^^

- Documentation review `#455 <https://github.com/ansys/pyspeos/pull/455>`_
- fix broken inner links `#465 <https://github.com/ansys/pyspeos/pull/465>`_
- fix make.bat clean call `#466 <https://github.com/ansys/pyspeos/pull/466>`_


Fixed
^^^^^

- missing get method for optical properties `#434 <https://github.com/ansys/pyspeos/pull/434>`_
- examples local run path was incorrect `#451 <https://github.com/ansys/pyspeos/pull/451>`_


Maintenance
^^^^^^^^^^^

- add new jobs and cleanup workflows `#425 <https://github.com/ansys/pyspeos/pull/425>`_
- general update/addition of files at project root level `#427 <https://github.com/ansys/pyspeos/pull/427>`_
- update python versions and dependencies `#443 <https://github.com/ansys/pyspeos/pull/443>`_
- add nightly workflow `#444 <https://github.com/ansys/pyspeos/pull/444>`_
- update code owners `#448 <https://github.com/ansys/pyspeos/pull/448>`_
- update labeler `#456 <https://github.com/ansys/pyspeos/pull/456>`_
- cleanup repo `#459 <https://github.com/ansys/pyspeos/pull/459>`_


Miscellaneous
^^^^^^^^^^^^^

- avoid mutable value as default value in function `#436 <https://github.com/ansys/pyspeos/pull/436>`_
- update architecture `#445 <https://github.com/ansys/pyspeos/pull/445>`_
- remove docker compose and update doc `#449 <https://github.com/ansys/pyspeos/pull/449>`_
- use __getitem__ in SpeosClient `#461 <https://github.com/ansys/pyspeos/pull/461>`_
- the core sensor, source, simulation class name `#462 <https://github.com/ansys/pyspeos/pull/462>`_

.. vale on