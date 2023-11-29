"""
Test basic intensity template database connection.
"""
import os

from ansys.speos.core.intensity_template import IntensityTemplateFactory
from ansys.speos.core.speos import Speos
from conftest import test_path


def test_intensity_template_factory(speos: Speos):
    """Test the intensity template factory."""
    assert speos.client.healthy is True
    # Get DB
    intens_t_db = speos.client.intensity_templates()  # Create intensity template stub from client channel

    # Library
    intens_t_lib = intens_t_db.create(
        message=IntensityTemplateFactory.library(
            name="library_0",
            description="library intensity template",
            file_uri=os.path.join(test_path, "IES_C_DETECTOR.ies"),
        )
    )
    assert intens_t_lib.key != ""

    # Lambertian
    intens_t_lamb = intens_t_db.create(
        message=IntensityTemplateFactory.lambertian(
            name="lambertian_0", description="lambertian intensity template", total_angle=180.0
        )
    )
    assert intens_t_lamb.key != ""

    # Cos
    intens_t_cos = intens_t_db.create(
        message=IntensityTemplateFactory.cos(name="cos_0", description="cos intensity template", N=3.0, total_angle=180.0)
    )
    assert intens_t_cos.key != ""

    # SymmetricGaussian
    intens_t_sym_gauss = intens_t_db.create(
        message=IntensityTemplateFactory.symmetric_gaussian(
            name="symmetric_gaussian_0",
            description="symmetric gaussian intensity template",
            FWHM_angle=30.0,
            total_angle=180.0,
        )
    )
    assert intens_t_sym_gauss.key != ""

    # AsymmetricGaussian
    intens_t_asym_gauss = intens_t_db.create(
        message=IntensityTemplateFactory.asymmetric_gaussian(
            name="asymmetric_gaussian_0",
            description="asymmetric gaussian intensity template",
            FWHM_angle_x=30.0,
            FWHM_angle_y=20.0,
            total_angle=180.0,
        )
    )
    assert intens_t_asym_gauss.key != ""

    # Delete all intensity_templates from DB
    for intens_t in intens_t_db.list():
        intens_t.delete()
