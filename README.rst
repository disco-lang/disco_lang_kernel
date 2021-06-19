A Jupyter kernel for the Disco language

This requires IPython 3.

To install::

    pip install disco_lang_kernel
    python -m disco_lang_kernel.install

To use it, run one of:

.. code:: shell

    jupyter notebook
    # In the notebook interface, select Disco from the 'New' menu
    jupyter qtconsole --kernel disco_lang
    jupyter console --kernel disco_lang

For details of how this works, see the Jupyter docs on `wrapper kernels
<http://jupyter-client.readthedocs.org/en/latest/wrapperkernels.html>`_, and
Pexpect's docs on the `replwrap module
<http://pexpect.readthedocs.org/en/latest/api/replwrap.html>`_
