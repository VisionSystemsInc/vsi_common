from sphinxcontrib.domaintools import custom_domain
import re

__version__ = "0.1"
# for this module's sphinx doc
release = __version__
version = release.rsplit('.', 1)[0]

def setup(app):
    app.add_domain(custom_domain('BashDomain',
        name  = 'bash',
        label = "Bourne Again Shell",

        elements = dict(
            file = dict(
                objname      = "Bash File",
                indextemplate = "pair: %s; Bash File",
            ),
            env = dict(
                objname = "Bash Environment Variable",
                indextemplate = "pair: %s; Bash Environment Variable"
            ),
            var = dict(
                objname = "Bash Variable",
                indextemplate = "pair: %s; Bash Variable"
            ),
            function = dict(
                objname = "Bash Function",
                indextemplate = "pair: %s; Bash Function"
            ),
        )))