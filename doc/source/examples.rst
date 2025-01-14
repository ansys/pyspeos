Examples
########

.. jinja:: main_toctree

    {% if build_examples %}


    Basic examples
    ==============

    This series of tutorials explains basic examples involving Speos objects using Python and PySpeos.

    .. nbgallery::
        :caption: Script layer examples

        examples/script-opt-prop
        examples/script-source
        examples/script-sensor
        examples/script-part
        examples/script-simulation
        examples/script-project
        examples/script-lpf-preview
        examples/script-prism-example

    .. nbgallery::
        :caption: Core layer examples

        examples/core-object-link
        examples/core-scene-job
        examples/core-modify-scene

    .. nbgallery::
        :caption: Workflow layer examples

        examples/workflow-open-result
        examples/workflow-combine-speos

    {% else %}

    .. warning::

        Set ``BUILD_EXAMPLES`` to ``true`` in your environment to build the
        examples.

    {% endif %}
