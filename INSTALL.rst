###############################################
Setup sigrok-meter on Python 3 with PySide2/Qt5
###############################################


************
Introduction
************

This documentation outlines how to install ``sigrok-meter`` on a
contemporary Linux or macOS machine. Please read it carefully.

Using a virtualenv to install ``sigrok-meter`` is considered best practice.
There are two variants:

1. Install PyGObject 3 for your Linux/macOS distribution Python.
   When using this variant, please use the ``--system-site-packages`` option
   to ``virtualenv``.

2. Install PyGObject 3 using ``pip``.
   When using this variant, you are completely isolated from the distribution
   Python, but you will need ``libffi`` instead. As this will need
   ``libffi >= 3.0``, there is a line how to tweak ``PKG_CONFIG_PATH`` to
   use a contemporary version provided by Homebrew. On a different environment,
   you might well omit that line.


***********
Get sources
***********

::

    git clone https://github.com/sigrokproject/sigrok-meter
    cd sigrok-meter


*********************
Install prerequisites
*********************

This section will guide you through installing PyGObject version 3,
the Python bindings to GLib.

Variant 1
=========

This uses the PyGObject package from your distribution Python.
::

    # Install PyGObject 3.
    brew install pygobject3
    apt-get install python3-gi

    # Create and activate virtualenv.
    virtualenv .venv39 --python=python3.9 --system-site-packages
    source .venv39/bin/activate


Variant 2
=========

This installs PyGObject using ``pip``.
::

    # Install libffi.
    brew install libffi
    apt-get install libffi6

    # Create and activate virtualenv.
    virtualenv .venv39 --python=python3.9
    source .venv39/bin/activate

    # Install PyGObject 3, needs libffi >= 3.0.
    export PKG_CONFIG_PATH="/usr/local/opt/libffi/lib/pkgconfig"
    pip install pygobject


********************
Install sigrok-meter
********************

This section illustrates how to populate the virtualenv with the prerequisites
needed for running ``sigrok-meter``.


libsigrok Python binding
========================

This assumes you successfully compiled ``libsigrok`` including its Python
bindings like::

    ../configure --enable-bindings --enable-cxx --enable-ruby=false --enable-java=false

Here we go::

    # Activate virtualenv.
    source .venv39/bin/activate

    # Install libsigrok Python binding. YMMV.
    pip install numpy
    python -m easy_install /path/to/libsigrok/build/bindings/python/dist/libsigrok-0.6.0-py3.9-macosx-10.13-x86_64.egg

Two additional notes:

1. You should install the same version of NumPy used when building ``libsigrok``.
2. If ``easy_install`` is missing on your machine, you might want to decide to
   downgrade ``setuptools`` within your virtualenv to the most recent version
   still including it by typing ``pip install "setuptools~=51.3"``.


Finally
=======

This will install the PySide2/Qt5 bindings and will instruct you how to compile
the Qt resource file into a Python representation, see also
`.qrc Files » Generating a Python file`_.

.. _.qrc Files » Generating a Python file: https://doc.qt.io/qtforpython/tutorials/basictutorial/qrcfiles.html#generating-a-python-file

::

    # Activate virtualenv.
    source .venv39/bin/activate

    # Install UI prerequisites.
    pip install pyside2 pyqtgraph

    # Sanity checks.
    ./test

    # Compile resources from "resources.qrc".
    make


*********
Testdrive
*********

Run ``sigrok-meter``::

    ./sigrok-meter --pyside --driver demo:analog_channels=1 --config samplerate=10:limit_samples=10

Enjoy.
