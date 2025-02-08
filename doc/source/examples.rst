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

        examples/workflow-open-result
        examples/workflow-combine-speos

    The series of basic examples below explains how to use different PySpeos core methods.

    .. nbgallery::
        :caption: Core examples

        examples/script-project
        examples/script-opt-prop
        examples/script-source
        examples/script-sensor
        examples/script-part
        examples/script-simulation
        examples/script-lpf-preview
        examples/script-prism-example


    The series of basic examples below explains how to use different core layer methods.

    .. nbgallery::
        :caption: Core layer examples

        examples/core-object-link
        examples/core-scene-job
        examples/core-modify-scene

    {% else %}

    .. warning::

        Set ``BUILD_EXAMPLES`` to ``true`` in your environment to build the
        examples.

    {% endif %}
