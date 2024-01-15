.. Copyright (C) 2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

****************************
How To's and Troubleshooting
****************************

Adding licensing information
============================

The pre-commit hooks in this repository check for compliance with `REUSE <https://reuse.software/>`_.
If the hooks fail you can add licensing information with the following command:

.. code-block:: shell
   :caption: Create licensing information with reuse in :guilabel:`VAGRANT`

   reuse annotate --copyright="Univention GmbH" \
                  --license="AGPL-3.0-only" \
                  --copyright-style="string-c" \
                  --template=univention \
                  --year "2024" \
                  --recursive \
                  --merge-copyrights \
                  --skip-unrecognised \
                  --skip-existing \
                  .

If after this command the hook still fails, it means that the repo contains some files for which the tool does not know
how to automatically add licensing information. In those cases you create a text file with the same name, but the suffix
``.license`` and the following content next to the file in question:

.. code-block:: text

   Copyright (C) 2024 Univention GmbH

   SPDX-License-Identifier: AGPL-3.0-only
