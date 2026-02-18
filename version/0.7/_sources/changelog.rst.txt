.. _ref_release_notes:

Release notes
#############

This document contains the release notes for the PySpeos project.

.. vale off

.. towncrier release notes start

`0.7.2 <https://github.com/ansys/pyspeos/releases/tag/v0.7.2>`_ - February 06, 2026
===================================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Source ambient environment
          - `#808 <https://github.com/ansys/pyspeos/pull/808>`_

        * - Source ambient environment - In 0.7
          - `#841 <https://github.com/ansys/pyspeos/pull/841>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Add Gaussian function and update R and T parts
          - `#837 <https://github.com/ansys/pyspeos/pull/837>`_

        * - Add Gaussian function and update R and T parts - in 0.7
          - `#840 <https://github.com/ansys/pyspeos/pull/840>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Speos launcher using pim - fix issue when getting target from channel
          - `#827 <https://github.com/ansys/pyspeos/pull/827>`_

        * - Speos launcher using pim - fix issue when getting target from channel - In 0.7
          - `#839 <https://github.com/ansys/pyspeos/pull/839>`_


`0.7.1 <https://github.com/ansys/pyspeos/releases/tag/v0.7.1>`_ - January 13, 2026
==================================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Add supporting virtual bsdf bench
          - `#763 <https://github.com/ansys/pyspeos/pull/763>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Bump ansys-sphinx-theme[autoapi] from 1.6.3 to 1.6.4 in the doc-deps group
          - `#793 <https://github.com/ansys/pyspeos/pull/793>`_

        * - Bump pytest from 9.0.1 to 9.0.2 in the test-deps group
          - `#795 <https://github.com/ansys/pyspeos/pull/795>`_

        * - Bump the jupyter-deps group across 1 directory with 2 updates
          - `#807 <https://github.com/ansys/pyspeos/pull/807>`_

        * - Bump psutil from 7.1.3 to 7.2.1
          - `#809 <https://github.com/ansys/pyspeos/pull/809>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Exclude vbb test from nightly run with 251
          - `#801 <https://github.com/ansys/pyspeos/pull/801>`_

        * - Nightly run
          - `#811 <https://github.com/ansys/pyspeos/pull/811>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Rework logic around vtk-osmesa
          - `#774 <https://github.com/ansys/pyspeos/pull/774>`_

        * - Bump ansys/actions from 10.2.2 to 10.2.3
          - `#791 <https://github.com/ansys/pyspeos/pull/791>`_

        * - Bump actions/checkout from 6.0.0 to 6.0.1
          - `#792 <https://github.com/ansys/pyspeos/pull/792>`_

        * - Bump codecov/codecov-action from 5.5.1 to 5.5.2
          - `#794 <https://github.com/ansys/pyspeos/pull/794>`_

        * - Update CHANGELOG for v0.7.0
          - `#796 <https://github.com/ansys/pyspeos/pull/796>`_

        * - Bump dev version into v0.7.dev0
          - `#797 <https://github.com/ansys/pyspeos/pull/797>`_

        * - Bump actions/download-artifact from 6.0.0 to 7.0.0
          - `#798 <https://github.com/ansys/pyspeos/pull/798>`_

        * - Bump actions/upload-artifact from 5.0.0 to 6.0.0
          - `#799 <https://github.com/ansys/pyspeos/pull/799>`_

        * - Pre-commit autoupdate
          - `#800 <https://github.com/ansys/pyspeos/pull/800>`_, `#805 <https://github.com/ansys/pyspeos/pull/805>`_

        * - Update year in headers
          - `#810 <https://github.com/ansys/pyspeos/pull/810>`_


`0.7.0 <https://github.com/ansys/pyspeos/releases/tag/v0.7.0>`_ - December 12, 2025
===================================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Update vtk-osmesa version to 9.3.1
          - `#756 <https://github.com/ansys/pyspeos/pull/756>`_

        * - Use grpc secure channel
          - `#783 <https://github.com/ansys/pyspeos/pull/783>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Bump the doc-deps group with 2 updates
          - `#723 <https://github.com/ansys/pyspeos/pull/723>`_

        * - Bump pytest-cov from 6.3.0 to 7.0.0 in the test-deps group
          - `#724 <https://github.com/ansys/pyspeos/pull/724>`_

        * - Update grpcio requirement from <1.75,>=1.50.0 to >=1.50.0,<1.76 in the grpc-deps group
          - `#735 <https://github.com/ansys/pyspeos/pull/735>`_

        * - Bump psutil from 7.0.0 to 7.1.0
          - `#737 <https://github.com/ansys/pyspeos/pull/737>`_

        * - Bump the jupyter-deps group across 1 directory with 2 updates
          - `#753 <https://github.com/ansys/pyspeos/pull/753>`_, `#781 <https://github.com/ansys/pyspeos/pull/781>`_

        * - Use autoapi target of ansys-sphinx-theme
          - `#754 <https://github.com/ansys/pyspeos/pull/754>`_

        * - Update grpcio requirement from <1.76,>=1.50.0 to >=1.50.0,<1.77 in the grpc-deps group
          - `#766 <https://github.com/ansys/pyspeos/pull/766>`_

        * - Bump psutil from 7.1.0 to 7.1.3
          - `#771 <https://github.com/ansys/pyspeos/pull/771>`_

        * - Bump pytest from 8.4.2 to 9.0.0 in the test-deps group
          - `#773 <https://github.com/ansys/pyspeos/pull/773>`_

        * - Bump the doc-deps group across 1 directory with 5 updates
          - `#789 <https://github.com/ansys/pyspeos/pull/789>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Update ``CONTRIBUTORS.md`` with the latest contributors
          - `#744 <https://github.com/ansys/pyspeos/pull/744>`_

        * - Fix typo in CONTRIBUTING.md
          - `#786 <https://github.com/ansys/pyspeos/pull/786>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Update CHANGELOG for v0.6.2
          - `#721 <https://github.com/ansys/pyspeos/pull/721>`_

        * - Pre-commit autoupdate
          - `#725 <https://github.com/ansys/pyspeos/pull/725>`_, `#757 <https://github.com/ansys/pyspeos/pull/757>`_, `#782 <https://github.com/ansys/pyspeos/pull/782>`_, `#790 <https://github.com/ansys/pyspeos/pull/790>`_

        * - Update CHANGELOG for v0.6.3
          - `#732 <https://github.com/ansys/pyspeos/pull/732>`_

        * - Add vulnerability check
          - `#738 <https://github.com/ansys/pyspeos/pull/738>`_

        * - Add security policy file
          - `#739 <https://github.com/ansys/pyspeos/pull/739>`_

        * - Add backwards compatibility test
          - `#740 <https://github.com/ansys/pyspeos/pull/740>`_, `#741 <https://github.com/ansys/pyspeos/pull/741>`_

        * - Bump ansys/actions from 10.0.20 to 10.1.2
          - `#745 <https://github.com/ansys/pyspeos/pull/745>`_

        * - Bump ansys/actions from 10.1.3 to 10.1.4
          - `#750 <https://github.com/ansys/pyspeos/pull/750>`_

        * - Bump docker/login-action from 3.5.0 to 3.6.0
          - `#751 <https://github.com/ansys/pyspeos/pull/751>`_

        * - Bump peter-evans/create-or-update-comment from 4.0.0 to 5.0.0
          - `#752 <https://github.com/ansys/pyspeos/pull/752>`_

        * - Bump actions/upload-artifact from 4.6.2 to 5.0.0
          - `#764 <https://github.com/ansys/pyspeos/pull/764>`_

        * - Bump actions/download-artifact from 5.0.0 to 6.0.0
          - `#765 <https://github.com/ansys/pyspeos/pull/765>`_

        * - Update missing or outdated files
          - `#769 <https://github.com/ansys/pyspeos/pull/769>`_

        * - Bump ansys/actions from 10.1.4 to 10.1.5
          - `#770 <https://github.com/ansys/pyspeos/pull/770>`_

        * - Adjust ansys tools path dependency
          - `#777 <https://github.com/ansys/pyspeos/pull/777>`_

        * - Bump actions/checkout from 5.0.0 to 6.0.0
          - `#779 <https://github.com/ansys/pyspeos/pull/779>`_

        * - Bump actions/setup-python from 6.0.0 to 6.1.0
          - `#784 <https://github.com/ansys/pyspeos/pull/784>`_

        * - Bump ansys/actions from 10.1.5 to 10.2.2
          - `#787 <https://github.com/ansys/pyspeos/pull/787>`_


  .. tab-item:: Miscellaneous

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Subprocess related line of codes
          - `#726 <https://github.com/ansys/pyspeos/pull/726>`_


`0.6.3 <https://github.com/ansys/pyspeos/releases/tag/v0.6.3>`_ - September 18, 2025
====================================================================================

.. tab-set::


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Append not supported scene data instance
          - `#727 <https://github.com/ansys/pyspeos/pull/727>`_

        * - Append not supported scene data instance (#727)
          - `#730 <https://github.com/ansys/pyspeos/pull/730>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Adapt docker run command for 25R2 sp2
          - `#722 <https://github.com/ansys/pyspeos/pull/722>`_

        * - Adapt docker run 25 r2sp2
          - `#729 <https://github.com/ansys/pyspeos/pull/729>`_

        * - Adapt docker run 25 r2sp2 (#729)
          - `#731 <https://github.com/ansys/pyspeos/pull/731>`_


`0.6.2 <https://github.com/ansys/pyspeos/releases/tag/v0.6.2>`_ - September 11, 2025
====================================================================================

.. tab-set::


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Add HTML context metadata
          - `#718 <https://github.com/ansys/pyspeos/pull/718>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Pre-commit autoupdate
          - `#716 <https://github.com/ansys/pyspeos/pull/716>`_

        * - Update CHANGELOG for v0.6.1
          - `#720 <https://github.com/ansys/pyspeos/pull/720>`_


`0.6.1 <https://github.com/ansys/pyspeos/releases/tag/v0.6.1>`_ - September 11, 2025
====================================================================================

.. tab-set::


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Update grpcio requirement from <1.71,>=1.50.0 to >=1.50.0,<1.73 in the grpc-deps group
          - `#617 <https://github.com/ansys/pyspeos/pull/617>`_

        * - Bump the jupyter-deps group across 1 directory with 2 updates
          - `#659 <https://github.com/ansys/pyspeos/pull/659>`_, `#700 <https://github.com/ansys/pyspeos/pull/700>`_

        * - Update pyvista requirement from <0.46,>=0.40.0 to >=0.40.0,<0.47 in the graphics-deps group
          - `#695 <https://github.com/ansys/pyspeos/pull/695>`_

        * - Update pyvista[jupyter] requirement from <0.46,>=0.43 to >=0.43,<0.47
          - `#697 <https://github.com/ansys/pyspeos/pull/697>`_

        * - Update grpcio requirement from <1.73,>=1.50.0 to >=1.50.0,<1.75 in the grpc-deps group
          - `#698 <https://github.com/ansys/pyspeos/pull/698>`_

        * - Install comtypes only for windows
          - `#704 <https://github.com/ansys/pyspeos/pull/704>`_

        * - Bump the test-deps group with 2 updates
          - `#714 <https://github.com/ansys/pyspeos/pull/714>`_

        * - Bump the doc-deps group across 1 directory with 5 updates
          - `#715 <https://github.com/ansys/pyspeos/pull/715>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Update readme, support features info
          - `#670 <https://github.com/ansys/pyspeos/pull/670>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Subpart commit modified to work when updating an existing subpart
          - `#664 <https://github.com/ansys/pyspeos/pull/664>`_

        * - Change default version to 252
          - `#687 <https://github.com/ansys/pyspeos/pull/687>`_

        * - Handle specificities of new server 25R2 SP1 and backward compatibility with previous servers.
          - `#717 <https://github.com/ansys/pyspeos/pull/717>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Pre-commit autoupdate
          - `#638 <https://github.com/ansys/pyspeos/pull/638>`_, `#689 <https://github.com/ansys/pyspeos/pull/689>`_, `#707 <https://github.com/ansys/pyspeos/pull/707>`_

        * - Update changelog for v0.6.0
          - `#665 <https://github.com/ansys/pyspeos/pull/665>`_

        * - Update docker tag to 252 for doc stage
          - `#668 <https://github.com/ansys/pyspeos/pull/668>`_

        * - Bump ansys/actions from 10.0.12 to 10.0.13
          - `#674 <https://github.com/ansys/pyspeos/pull/674>`_

        * - Pin vtk-osmesa version
          - `#675 <https://github.com/ansys/pyspeos/pull/675>`_

        * - Bump docker/login-action from 3.4.0 to 3.5.0
          - `#692 <https://github.com/ansys/pyspeos/pull/692>`_

        * - Bump ansys/actions from 10.0.13 to 10.0.14
          - `#693 <https://github.com/ansys/pyspeos/pull/693>`_

        * - Bump actions/download-artifact from 4.3.0 to 5.0.0
          - `#694 <https://github.com/ansys/pyspeos/pull/694>`_

        * - Bump actions/checkout from 4.2.2 to 5.0.0
          - `#701 <https://github.com/ansys/pyspeos/pull/701>`_

        * - Bump codecov/codecov-action from 5.4.3 to 5.5.0
          - `#702 <https://github.com/ansys/pyspeos/pull/702>`_

        * - Bump pypa/gh-action-pypi-publish from 1.12.4 to 1.13.0
          - `#709 <https://github.com/ansys/pyspeos/pull/709>`_

        * - Bump actions/labeler from 5.0.0 to 6.0.1
          - `#710 <https://github.com/ansys/pyspeos/pull/710>`_

        * - Bump actions/setup-python from 5.6.0 to 6.0.0
          - `#711 <https://github.com/ansys/pyspeos/pull/711>`_

        * - Bump codecov/codecov-action from 5.5.0 to 5.5.1
          - `#712 <https://github.com/ansys/pyspeos/pull/712>`_

        * - Bump ansys/actions from 10.0.14 to 10.0.20
          - `#713 <https://github.com/ansys/pyspeos/pull/713>`_


  .. tab-item:: Test

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Core - sub part - check that modifying sub part's axis system i…
          - `#671 <https://github.com/ansys/pyspeos/pull/671>`_


`0.6.0 <https://github.com/ansys/pyspeos/releases/tag/v0.6.0>`_ - July 15, 2025
===============================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Kernel - facestub - add create_batch and read_batch methods
          - `#369 <https://github.com/ansys/pyspeos/pull/369>`_

        * - enhance the project preview: luminaire, surface, rayfile
          - `#561 <https://github.com/ansys/pyspeos/pull/561>`_

        * - lightexpert
          - `#592 <https://github.com/ansys/pyspeos/pull/592>`_

        * - Add 3d irradiance
          - `#595 <https://github.com/ansys/pyspeos/pull/595>`_

        * - Add version warnings
          - `#608 <https://github.com/ansys/pyspeos/pull/608>`_

        * - Spectralbsdf
          - `#614 <https://github.com/ansys/pyspeos/pull/614>`_

        * - Add method to export simulation
          - `#629 <https://github.com/ansys/pyspeos/pull/629>`_

        * - Add natural light
          - `#633 <https://github.com/ansys/pyspeos/pull/633>`_

        * - Add export result as vtp files
          - `#643 <https://github.com/ansys/pyspeos/pull/643>`_

        * - Add cad visual data property
          - `#661 <https://github.com/ansys/pyspeos/pull/661>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - bump ansys-api-speos from 0.14.2 to 0.15.2
          - `#589 <https://github.com/ansys/pyspeos/pull/589>`_

        * - bump the doc-deps group with 3 updates
          - `#604 <https://github.com/ansys/pyspeos/pull/604>`_

        * - bump notebook from 7.4.2 to 7.4.3 in the jupyter-deps group across 1 directory
          - `#609 <https://github.com/ansys/pyspeos/pull/609>`_

        * - Bump ansys-sphinx-theme from 1.5.0 to 1.5.2 in the doc-deps group
          - `#616 <https://github.com/ansys/pyspeos/pull/616>`_

        * - Bump pytest from 8.3.5 to 8.4.0 in the test-deps group
          - `#618 <https://github.com/ansys/pyspeos/pull/618>`_

        * - Bump pytest-cov from 6.1.1 to 6.2.1 in the test-deps group
          - `#623 <https://github.com/ansys/pyspeos/pull/623>`_

        * - Bump pytest from 8.4.0 to 8.4.1 in the test-deps group
          - `#637 <https://github.com/ansys/pyspeos/pull/637>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Add badges into readme.rst
          - `#610 <https://github.com/ansys/pyspeos/pull/610>`_

        * - Adjust missing examples
          - `#612 <https://github.com/ansys/pyspeos/pull/612>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - add message size to nighly ci
          - `#600 <https://github.com/ansys/pyspeos/pull/600>`_

        * - Only reset the _visual_data when graphics_available is true
          - `#621 <https://github.com/ansys/pyspeos/pull/621>`_

        * - Read empty mesh when no body at root and subpart.1
          - `#632 <https://github.com/ansys/pyspeos/pull/632>`_

        * - Duplicated feature that is already inside the _features list
          - `#636 <https://github.com/ansys/pyspeos/pull/636>`_

        * - 640 camera with distortion v2 to v4
          - `#644 <https://github.com/ansys/pyspeos/pull/644>`_

        * - Sim export_unittest for windows
          - `#655 <https://github.com/ansys/pyspeos/pull/655>`_

        * - Kernel - faceactions - check if batch is available on server - if available use batch project _fill_bodies
          - `#656 <https://github.com/ansys/pyspeos/pull/656>`_

        * - Print of protobuf messages containing special characters
          - `#663 <https://github.com/ansys/pyspeos/pull/663>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - update CHANGELOG for v0.5.0
          - `#597 <https://github.com/ansys/pyspeos/pull/597>`_

        * - bump dev version into v0.6.dev0
          - `#598 <https://github.com/ansys/pyspeos/pull/598>`_

        * - pre-commit autoupdate
          - `#599 <https://github.com/ansys/pyspeos/pull/599>`_

        * - update CHANGELOG for v0.5.1
          - `#602 <https://github.com/ansys/pyspeos/pull/602>`_

        * - bump ansys/actions from 9.0.11 to 9.0.13
          - `#606 <https://github.com/ansys/pyspeos/pull/606>`_

        * - Pre-commit autoupdate
          - `#611 <https://github.com/ansys/pyspeos/pull/611>`_, `#619 <https://github.com/ansys/pyspeos/pull/619>`_

        * - Bump ansys/actions into v10.0.3
          - `#613 <https://github.com/ansys/pyspeos/pull/613>`_

        * - Bump ansys/actions from 10.0.3 to 10.0.8
          - `#615 <https://github.com/ansys/pyspeos/pull/615>`_

        * - Bump ansys/actions from 10.0.8 to 10.0.11
          - `#622 <https://github.com/ansys/pyspeos/pull/622>`_

        * - Update dependabot cfg and code owners
          - `#627 <https://github.com/ansys/pyspeos/pull/627>`_

        * - Bump ansys/actions from 10.0.11 to 10.0.12
          - `#649 <https://github.com/ansys/pyspeos/pull/649>`_


  .. tab-item:: Test

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Add several tests for file transfer api
          - `#652 <https://github.com/ansys/pyspeos/pull/652>`_


`0.5.1 <https://github.com/ansys/pyspeos/releases/tag/v0.5.1>`_ - May 28, 2025
==============================================================================

.. tab-set::


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - coding error, switch to correct order
          - `#601 <https://github.com/ansys/pyspeos/pull/601>`_


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