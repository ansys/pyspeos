Examples
########

.. jinja:: main_toctree

    {% if build_examples %}


    Basic examples
    ==============

    This series of tutorials explains basic examples involving Speos objects using Python and PySpeos.

    .. nbgallery::
        :caption: Core layer examples

        examples/core-object-link
        examples/core-scene-job

    {% else %}

    .. warning::

        Set ``BUILD_EXAMPLES`` to ``true`` in your environment to build the
        examples.

    {% endif %}
