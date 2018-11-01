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

from sphinx.locale import __
from sphinx.util import logging
logger = logging.getLogger(__name__)

__version__ = '0.1'


class GenericObject(ObjectDescription):
  """
  #  A generic x-ref directive registered with Sphinx.add_object_type().

  Usage:
      DomainObject = type('DomainObject', (GenericObject, object), dict(
          domain = 'my-domain-name'))

      DomainObject = type('DomainObject', (GenericObject, object), dict(
          domain = 'my-domain-name', indextemplate=(

      class MyDescriptionObject(GenericObject):
  """
  indextemplate = ''
  parse_node = None
  domain = 'std'

  # The signature of the urls that get auto generated AND the link names
  # In other words, remove the arguments
  def handle_signature(self, sig, signode):
    if self.parse_node:
      name = self.parse_node(self.options, self.env, sig, signode)
    else:
      logger.warning(__('Default Signature handler used for: "%s"'), sig, location=__file__)
      signode.clear()
      signode += addnodes.desc_name(sig, sig)
      # normalize whitespace like XRefRole does
      name = ws_re.sub('', sig)
    return name

  def add_target_and_index(self, name, sig, signode):
    targetname = '%s-%s' % (self.objtype, name)
    signode['ids'].append(targetname)
    self.state.document.note_explicit_target(signode)
    if self.indextemplate:
      colon = self.indextemplate.find(':')
      if colon != -1:
        indextype = self.indextemplate[:colon].strip()
        indexentry = self.indextemplate[colon+1:].strip() % (name,)
      else:
        indextype = 'single'
        indexentry = self.indextemplate % (name,)
      self.indexnode['entries'].append((indextype, indexentry,
                                          targetname, '', None))
    self.env.domaindata[self.domain]['objects'][self.objtype, name] = \
        self.env.docname, targetname

  def before_content(self):
    # TOTALLY undocumented feature
    if self.objtype == "file":
      self.env.ref_context['bash:file'] = self.names[-1]
    elif self.objtype == "function":
      self.env.ref_context['bash:function'] = self.names[-1]

class CustomDomain(Domain):
  """
  Domain for all objects that don't fit into another domain or are added
  via the application interface.
  """

  name = 'std'
  label = 'Default'

  object_types = {}
  directives = {}
  roles = {}
  initial_data = {
      'objects': {},      # (type, name) -> docname, labelid
  }
  dangling_warnings = {}

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


def custom_domain(class_name, name='', label='', elements = {}):
  '''create a custom domain

  For each given element there are created a directive and a role
  for referencing and indexing.

  :param class_name: ClassName of your new domain (e.g. `GnuMakeDomain`)
  :param name      : short name of your domain (part of directives, e.g. `make`)
  :param label     : Long name of your domain (e.g. `GNU Make`)
  :param elements  :
      dictionary of your domain directives/roles

      An element value is a dictionary with following possible entries:

      - `objname` - Long name of the entry, defaults to entry's key

      - `role` - role name, defaults to entry's key

      - `indextemplate` - e.g. ``pair: %s; Make Target``, where %s will be
        the matched part of your role.  You may leave this empty, defaults
        to ``pair: %s; <objname>``

      - `parser` - a function with signature ``(env, sig, signode)``,
        defaults to `None`.

      - `fields` - A list of fields where parsed fields are mapped to. this
        is passed to Domain as `doc_field_types` parameter.

      - `ref_nodeclass` - class passed as XRefRole's innernodeclass,
        defaults to `None`.

  '''
  domain_class = type(class_name, (CustomDomain, object), dict(
      name  = name,
      label = label,
  ))

  domain_object_class = \
      type("%s_Object"%name, (GenericObject, object), dict(domain=name))

  for n,e in elements.items():
    obj_name = e.get('objname', n)
    domain_class.object_types[n] = ObjType(
        obj_name, e.get('role', n) )

    domain_class.directives[n] = type(n, (domain_object_class, object), dict(
        indextemplate   = e.get('indextemplate', 'pair: %%s; %s' % obj_name),
        parse_node      = staticmethod(e.get('parse_node', None)),
        doc_field_types = e.get('fields', []),
        ))

    # domain_class.roles[e.get('role', n)] = XRefRole(innernodeclass=
        # e.get('ref_nodeclass', None))
    domain_class.roles[e.get('role', n)] = e.get('xref_role', XRefRole(innernodeclass=e.get('ref_nodeclass', None)))

  return domain_class

__version__ = "0.1"
# for this module's sphinx doc
release = __version__
version = release.rsplit('.', 1)[0]

function_sig_re = re.compile(r'^([\w.-]+)( (.*))?')

def parse_bash(options, env, sig, signode, sigtype='unknown'):

  # ref_name - name used for href. Also needed for domain references. Python
  #            has a way of not needing the module/class scope part. I don't
  #            see how, so in the end, I don't care.
  # full_name - The name that that reader sees when reading the document
  #

  m = function_sig_re.match(sig)
  if not m:
    logger.warning(__('Signature does not match pattern: "%s"'), sig, location=__file__)
    signode.clear()
    signode += addnodes.desc_name(sig, sig)
    # normalize whitespace like XRefRole does
    return ws_re.sub('', sig)

  name, _, args = m.groups()

  filename = env.ref_context.get('bash:file')
  functionname = env.ref_context.get('bash:function')

  if filename:
    signode['file'] = filename

  ref_name = name
  fullname = name

  if sigtype in ['command', 'function', 'env', 'var'] and (functionname or filename):

    if sigtype in ['command']:
      if functionname:
        fullname = functionname + " " + fullname
      # Filename is already prepended to funcitonname
      elif filename:
        fullname = filename + " " + fullname
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

def setup(app):
  app.add_domain(custom_domain(
      'BashDomain',
      name  = 'bash',
      label = "Bourne Again Shell",

      elements = dict(
          file = dict(
              objname = "Bash File",
              parse_node = lambda a,b,c,d: parse_bash(a,b,c,d,'file'),
              indextemplate = "pair: %s; Bash File",
              # Don't need the xref_role for files
          ),
          env = dict(
              objname = "Bash Environment Variable",
              parse_node = lambda a,b,c,d: parse_bash(a,b,c,d,'env'),
              indextemplate = "pair: %s; Bash Environment Variable",
              xref_role = BashXRefRole()
          ),
          var = dict(
              objname = "Bash Variable",
              parse_node = lambda a,b,c,d: parse_bash(a,b,c,d,'var'),
              indextemplate = "pair: %s; Bash Variable",
              xref_role = BashXRefRole()
          ),
          function = dict(
              objname = "Bash Function",
              role = "func",
              parse_node = lambda a,b,c,d: parse_bash(a,b,c,d,'function'),
              indextemplate = "pair: %s; Bash Function",
              xref_role = BashXRefRole()
          ),
          command = dict(
              objname = "Just command",
              role = "cmd",
              parse_node = lambda a,b,c,d: parse_bash(a,b,c,d,'command'),
              indextemplate = "pair: %s; Just command",
              xref_role = BashXRefRole()
          ),
      )))