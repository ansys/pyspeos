import typing

import numpy

from ansys.speos.core import Body, Face, GeoRef, Part, Project, Speos


def create_rectangle(
    face: Face,
    pt_center,
    x_axis,
    y_axis,
    x_size,
    y_size,
    geo_ref_context=GeoRef(name="", description="", metadata={}),
) -> GeoRef:
    if len(pt_center) != 3 or len(x_axis) != 3 or len(y_axis) != 3:
        raise ValueError("array with length 3 was expected")

    np_pt_center = numpy.array(pt_center)
    np_x_axis = numpy.array(x_axis)
    np_y_axis = numpy.array(y_axis)
    pt_0 = np_pt_center - (0.5 * x_size) * np_x_axis - (0.5 * y_size) * np_y_axis
    pt_1 = np_pt_center + (0.5 * x_size) * np_x_axis - (0.5 * y_size) * np_y_axis
    pt_2 = np_pt_center + (0.5 * x_size) * np_x_axis + (0.5 * y_size) * np_y_axis
    pt_3 = np_pt_center - (0.5 * x_size) * np_x_axis + (0.5 * y_size) * np_y_axis

    print(str(pt_0))
    print(str(pt_1))
    print(str(pt_2))
    print(str(pt_3))

    pt_array = numpy.concatenate((pt_0, pt_1, pt_2, pt_3))
    normal = numpy.cross(x_axis, y_axis)
    normals = numpy.concatenate((normal, normal, normal, normal))

    face.set_vertices(pt_array)
    face.set_normals(normals)
    face.set_facets([0, 1, 3, 1, 2, 3])

    face.commit()

    if geo_ref_context.has_native_link():
        return geo_ref_context.join_native_link(GeoRef.from_native_link(geopath=face._name))
    else:
        return GeoRef.from_native_link(geopath=face._name)


def create_box(
    body: Body,
    base_axis_sytem,
    x_size,
    y_size,
    z_size,
    geo_ref_context=GeoRef(name="", description="", metadata={}),
) -> typing.List[GeoRef]:
    np_axis_system = numpy.array(base_axis_sytem)
    np_axis_system = np_axis_system.reshape(4, 3)
    np_origin = np_axis_system[0, :]
    np_x_axis = np_axis_system[1, :]
    np_y_axis = np_axis_system[2, :]
    np_z_axis = np_axis_system[3, :]

    index = 0

    if geo_ref_context.has_native_link():
        body_geo_ref = geo_ref_context.join_native_link(GeoRef.from_native_link(body._name))
    else:
        body_geo_ref = GeoRef.from_native_link(body._name)
    geo_paths = [body_geo_ref]
    geo_paths.append(
        create_rectangle(
            face=body.create_face(name="face:" + str(index)),
            geo_ref_context=body_geo_ref,
            pt_center=np_origin - 0.5 * z_size * np_z_axis,
            x_axis=-np_x_axis,
            y_axis=np_y_axis,
            x_size=x_size,
            y_size=y_size,
        )
    )
    index += 1
    geo_paths.append(
        create_rectangle(
            face=body.create_face(name="face:" + str(++index)),
            geo_ref_context=body_geo_ref,
            pt_center=np_origin + 0.5 * z_size * np_z_axis,
            x_axis=np_x_axis,
            y_axis=np_y_axis,
            x_size=x_size,
            y_size=y_size,
        )
    )
    index += 1
    geo_paths.append(
        create_rectangle(
            face=body.create_face(name="face:" + str(++index)),
            geo_ref_context=body_geo_ref,
            pt_center=np_origin - 0.5 * x_size * np_x_axis,
            x_axis=np_z_axis,
            y_axis=np_y_axis,
            x_size=z_size,
            y_size=y_size,
        )
    )
    index += 1
    geo_paths.append(
        create_rectangle(
            face=body.create_face(name="face:" + str(++index)),
            geo_ref_context=body_geo_ref,
            pt_center=np_origin + 0.5 * x_size * np_x_axis,
            x_axis=-np_z_axis,
            y_axis=np_y_axis,
            x_size=z_size,
            y_size=y_size,
        )
    )
    index += 1
    geo_paths.append(
        create_rectangle(
            face=body.create_face(name="face:" + str(++index)),
            geo_ref_context=body_geo_ref,
            pt_center=np_origin - 0.5 * y_size * np_y_axis,
            x_axis=np_x_axis,
            y_axis=np_z_axis,
            x_size=x_size,
            y_size=z_size,
        )
    )
    index += 1
    geo_paths.append(
        create_rectangle(
            face=body.create_face(name="face:" + str(++index)),
            geo_ref_context=body_geo_ref,
            pt_center=np_origin + 0.5 * y_size * np_y_axis,
            x_axis=np_x_axis,
            y_axis=-np_z_axis,
            x_size=x_size,
            y_size=z_size,
        )
    )

    body.commit()
    return geo_paths
