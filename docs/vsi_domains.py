# -*- coding: utf-8 -*-
"""
    sphinxcontrib.domaintools
    =========================

    Code is taken from `sphinx.domains.std`_ and is
    parameterized for easy domain creation.

    :copyright: Kay-Uwe (Kiwi) Lorenz, ModuleWorks GmbH
    :license: BSD, see LICENSE.txt for details


    sphinx.domains.std
    ~~~~~~~~~~~~~~~~~~

    The standard domain.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import unicodedata

from docutils import nodes

from sphinx import addnodes
from sphinx.roles import XRefRole
from sphinx.locale import l_, _
from sphinx.domains import Domain, ObjType
from sphinx.directives import ObjectDescription
from sphinx.util import ws_re
from sphinx.util.nodes import clean_astext, make_refnode
from typing import Tuple

from sphinx.locale import __
from sphinx.util import logging
logger = logging.getLogger(__name__)


from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
from typing import List, Tuple
from typing import cast
from docutils.nodes import Node


__version__ = "0.1"
# for this module's sphinx doc
release = __version__
version = release.rsplit('.', 1)[0]

function_sig_re = re.compile(r'^([\w.-]+)( (.*))?')


class BashObject(ObjectDescription):
  """
  #  A generic x-ref directive registered with Sphinx.add_object_type().

  Usage:
      DomainObject = type('DomainObject', (GenericObject, object), dict(
          domain = 'my-domain-name'))

      DomainObject = type('DomainObject', (GenericObject, object), dict(
          domain = 'my-domain-name', indextemplate=(

      class MyDescriptionObject(GenericObject):
  """
  domain = 'bash'
  doc_field_types = []

  def parse_node(self, options, env, sig, signode, sigtype='unknown'):

    # ref_name - name used for href. Also needed for domain references. Python
    #            has a way of not needing the module/class scope part. I don't
    #            see how, so in the end, I don't care.
    # full_name - The name that that reader sees when reading the document
    #

    m = function_sig_re.match(sig)
    if not m:
      name = sig
      args = ''
      logger.debug(__('Signature did not match pattern: "%s"'), name, location=__file__)
    else:
      name, _, args = m.groups()

    filename = env.ref_context.get('bash:file')
    functionname = env.ref_context.get('bash:function')

    if filename:
      signode['file'] = filename

    ref_name = name
    fullname = name

    if sigtype in ['command', 'function', 'env', 'var'] and (functionname or filename):

      if sigtype in ['command']:
        # if functionname:
        #   fullname = functionname + " " + fullname.replace('_', ' ')
        # # Filename is already prepended to funcitonname
        # elif filename:
        #   fullname = filename + " " + fullname.replace('_', ' ')
        fullname = "just " + fullname.replace('_', ' ')
        signode += addnodes.desc_addname(fullname , fullname)
      else:
        signode += addnodes.desc_name(fullname , fullname)

      if functionname and sigtype not in ['function', 'file']:
        ref_name = functionname + " " + ref_name
      # Filename is already prepended to funcitonname
      elif filename and sigtype not in ['file']:
        ref_name = filename + " " + ref_name
    else:
      signode += addnodes.desc_name(name, name)


    if args:
      args = args.split(' ')
      for arg in args:
        # white spaces are striped, use unicode! :D
        signode += addnodes.desc_annotation('\u00A0'+arg, '\u00A0'+arg)
    return ref_name


  # The signature of the urls that get auto generated AND the link names
  # In other words, remove the arguments
  def handle_signature(self, sig, signode):
    name = self.parse_node(self.options, self.env, sig, signode, self.objtype)
    return name

  def get_index_text(self, modname: str, name: str) -> str:
    if self.objtype == 'file':
      return "%s (file)" % (name),
    elif self.objtype == 'env':
      return "%s (environment variable)" % (name),
    elif self.objtype == 'var':
      return "%s (variable)" % (name),
    elif self.objtype == 'function':
      return "%s() (function)" % (name),
    elif self.objtype == 'command':
      return "%s (just command)" % (name),
    return ''

  def add_target_and_index(self, name, sig, signode):
    filename = self.env.ref_context.get('bash:file')
    # function = self.env.ref_context.get('bash:function')

    targetname = '%s-%s' % (self.objtype, name)
    signode['ids'].append(targetname)
    self.state.document.note_explicit_target(signode)

    indextext = self.get_index_text(filename, name)
    # if self.indextemplate:
      # colon = self.indextemplate.find(':')
      # if colon != -1:
        # indextype = self.indextemplate[:colon].strip()
        # indexentry = self.indextemplate[colon+1:].strip() % (name,)
      # else:
        # indextype = 'single'
        # indexentry = self.indextemplate % (name,)
    self.indexnode['entries'].append(('single', indextext,
                                     targetname, '', None))
    self.env.domaindata[self.domain]['objects'][self.objtype, name] = \
        self.env.docname, targetname

  def before_content(self):
    # TOTALLY undocumented feature
    if self.objtype == "file":
      self.env.ref_context['bash:file'] = self.names[-1]
    elif self.objtype == "function":
      self.env.ref_context['bash:function'] = self.names[-1]


# This class is responsible for auto appending filename/function name to
# reference if one is not already appended. It only works if there is no spaced
# in the target name, in bash this works well
class BashXRefRole(XRefRole):
  def process_link(self, env, refnode, has_explicit_title, title, target):
    role = refnode['reftype']

    if ' ' not in target:
      filename = env.ref_context.get('bash:file')
      functionname = env.ref_context.get('bash:function')

      # functionname contains filename already
      if functionname and role != 'func':
        target = functionname + " " + target
      elif filename:
        target = filename + " " + target

    return title, ws_re.sub(' ', target)


class BashFile(SphinxDirective):
    """
    Directive to mark description of a new module.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
      'platform': lambda x: x,
      'synopsis': lambda x: x,
      'noindex': directives.flag,
      'deprecated': directives.flag,
    }

    def run(self) -> List[Node]:
      domain = cast(BashDomain, self.env.get_domain('bash'))

      filename = self.arguments[0].strip()
      noindex = 'noindex' in self.options
      self.env.ref_context['bash:file'] = filename
      ret = []  # type: List[Node]
      if not noindex:
          # note module to the domain
          # domain.note_files(filename)
          # domain.note_object(filename, 'file', location=(self.env.docname, self.lineno))

          targetnode = nodes.target('', '', ids=['file-' + filename],
                                    ismod=True)
          # self.state.document.note_explicit_target(targetnode)
          # the platform and synopsis aren't printed; in fact, they are only
          # used in the modindex currently
          ret.append(targetnode)
          indextext = _('%s (file)') % filename
          inode = addnodes.index(entries=[('single', indextext,
                                            'file-' + filename, '', None)])
          ret.append(inode)
      return ret


class BashDomain(Domain):
  """
  Domain for all objects that don't fit into another domain or are added
  via the application interface.
  """

  name = 'bash'
  label = 'Bourne Again Shell'

  # files = {}
  initial_data = {
      'objects': {},      # (type, name) -> docname, labelid
  }
  dangling_warnings = {}

  object_types = {
    'file':     ObjType(_('file'),     'file'),
    'env':      ObjType(_('env'),      'env'),
    'var':      ObjType(_('var'),      'var'),
    'function': ObjType(_('function'), 'func'),
    'command':  ObjType(_('command'),  'cmd')
  }
  directives = {
    'file':     BashFile,
    'env':      BashObject,
    'var':      BashObject,
    'function': BashObject,
    'command':  BashObject
  }

  roles = {
    'file': XRefRole(innernodeclass=None),
    'env':  XRefRole(innernodeclass=BashXRefRole()),
    'var':  XRefRole(innernodeclass=BashXRefRole()),
    'func': XRefRole(innernodeclass=BashXRefRole()),
    'cmd':  XRefRole(innernodeclass=BashXRefRole())
  }

  # def note_files(self, filename: str) -> None:
  #     self.files[filename] = self.env.docname

  def clear_doc(self, docname):
    if 'objects' in self.data:
      self.data['objects'] = {key:val for key, val in self.data['objects'].items() if val[0] != docname}

  def resolve_xref(self, env, fromdocname, builder,
                   typ, target, node, contnode):
    objtypes = self.objtypes_for_role(typ) or []
    for objtype in objtypes:
      if (objtype, target) in self.data['objects']:
        docname, labelid = self.data['objects'][objtype, target]
        break
    else:
      docname, labelid = '', ''
    if not docname:
      return None
    return make_refnode(builder, fromdocname, docname,
                        labelid, contnode)

  def get_objects(self):
    for (type, name), info in self.data['objects'].items():
      yield (name, name, type, info[0], info[1],
             self.object_types[type].attrs['searchprio'])

  def get_type_name(self, type, primary=False):
    # never prepend "Default"
    return type.lname


def setup(app):
  app.add_domain(BashDomain)