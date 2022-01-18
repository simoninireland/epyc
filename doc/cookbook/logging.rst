.. _logging

.. currentmodule:: epyc

Getting access to more run-time information
-------------------------------------------

**Problem**: You need to get more information out of ``epyc``.

**Solution**: ``epyc`` makes use of Python's standard ``logging``
module. Various operations emit logging messages that can be
intercepted and used in various ways.

``epyc`` uses its own logger, whose name is stored in the constant
``epyc.Logger``: unsurprisingly it is called "epyc". You can
use this name to configure the details of logging that ``epyc``
performs. For example, if you want to suppress all messages except for
those that are errors (or worse), you could use code such as:

.. code-block:: python

   import logging
   import epyc

   epycLogger = logging.getLogger(epyc.Logger)
   epycLogger.setLevel(logging.ERROR)

There are lots of other configuration options, including logging to
files or to management services: see `the Python logging
HOWTO <https://docs.python.org/3/howto/logging.html>`_ for details.
