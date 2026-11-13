.. _migration_guide:

Migration guide
===============

This guide provides information on breaking changes, how to migrate
from one version of pyspeos to another, and other upstream dependencies that
have been updated.

Version ``0.8.0``
-----------------
- A big refactor of the codebase was done to make it more modular and easier to maintain. This
  causes some breaking changes in the API. The main point of the refactor was to remove set methods
  as much as possible and replace them by python properties. Below you can see an example of
  how to migrate from the old API to the new one based on setting vertices of a face:

.. code:: python

    from ansys.speos.core import Body, Face, Part, Project, Speos

    speos = launch_local_speos_rpc_server()
    p = Project(speos=speos)
    root_part = p.create_root_part().commit()
    body_b1 = root_part.create_body(name="TheBodyB1").commit()
    face_f1 = body_b1.create_face(name="TheFaceF1").commit()
    # Old API not working API
    face_f1.set_vertices([0, 0, 0, 1, 0, 0, 1, 1, 0]).set_facets([0, 1, 2]).set_normals([0,0,1,0,0,1,0,0,1]).commit()
    # New API
    face_f1.vertices = [0, 0, 0, 1, 0, 0, 1, 1, 0]
    face_f1.facets = [0, 1, 2]
    face_f1.normals = [0,0,1,0,0,1,0,0,1]
    face_f1.commit()

