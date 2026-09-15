.. _ref_examples:

Examples
########

.. jinja:: main_toctree

    {% if build_examples %}


    Basic examples
    ==============

    This series of tutorials explains basic examples involving Speos objects using Python and PySpeos.

    The series of workflow examples below demonstrate use cases using PySpeos core methods.

    .. nbgallery::
        :caption: Workflow examples

        examples/workflow/open-result
        examples/workflow/combine-speos

    The series of basic examples below explains how to use different PySpeos core methods.

    .. nbgallery::
        :caption: Core examples

        examples/core/project
        examples/core/opt-prop
        examples/core/source
        examples/core/sensor
        examples/core/part
        examples/core/simulation
        examples/core/lpf-preview
        examples/core/prism-example


    The series of basic examples below explains how to use different PySpeos kernel methods.

    .. nbgallery::
        :caption: Kernel examples

        examples/kernel/object-link
        examples/kernel/scene-job
        examples/kernel/modify-scene

    {% else %}

    .. warning::

        Set ``BUILD_EXAMPLES`` to ``true`` in your environment to build the
        examples.

    {% endif %}
