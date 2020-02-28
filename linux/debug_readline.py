#!/usr/bin/env python
import sys
from os import environ as env
import os

from pygments.lexers.shell import BashLexer
from pygments.styles import get_style_by_name

import prompt_toolkit
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
if prompt_toolkit.__version__[0:2] != "1.":
  from prompt_toolkit import PromptSession
  from prompt_toolkit.lexers import PygmentsLexer
  from prompt_toolkit.styles.pygments import style_from_pygments_cls
  from prompt_toolkit.key_binding import KeyBindings


  def key_bindings():
    key_binding = KeyBindings()
    key_binding.add('enter')(return_handler)
    key_binding.add('tab')(tab_handler)
    return key_binding

  def return_handler(event):
    buffer = event.current_buffer
    # document = buffer.document
    if buffer.text.endswith("\\"):
      buffer.text=buffer.text[:-1]+'\n'
    else:
      buffer.validate_and_handle()

  def tab_handler(event):
    buffer = event.current_buffer
    document = buffer.document
    if buffer.auto_suggest:
      suggestion = buffer.auto_suggest.get_suggestion(buffer, document)
      if suggestion.text:
        buffer.text+=suggestion.text
        buffer.cursor_position+=len(suggestion.text)

  def prompt_continuation(width, line_number, is_soft_wrap):
    return ' '*(width-2) + "… "


  style = style_from_pygments_cls(get_style_by_name(env.get(
      '_debug_read_color_scheme', 'vim')))
  session = PromptSession(message=env.get('_debug_prompt', '$ '),
                          lexer=PygmentsLexer(BashLexer),
                          style=style,
                          key_bindings=key_bindings(),
                          history=FileHistory(env.get('JUST_DEBUG_HISTORY',
                              os.path.expanduser('~/.debug_bash_history'))+'3'),
                          enable_history_search=True,
                          multiline=True,
                          auto_suggest=AutoSuggestFromHistory(),
                          prompt_continuation=prompt_continuation)

  try:
    text = session.prompt()
    sys.stderr.write(text)
  except KeyboardInterrupt:
    pass
else:
  # from __future__ import unicode_literals
  from prompt_toolkit import prompt
  from prompt_toolkit.styles import style_from_pygments
  from prompt_toolkit.layout.lexers import PygmentsLexer
  from prompt_toolkit.key_binding.manager import KeyBindingManager
  from prompt_toolkit.keys import Keys

  manager = KeyBindingManager.for_prompt()

  @manager.registry.add_binding(Keys.Enter)
  def return_handler(event):
    buffer = event.current_buffer
    if buffer.text.endswith("\\"):
      buffer.text=buffer.text[:-1]+'\n'
    else:
      buffer.accept_action.validate_and_handle(event.cli, buffer)

  @manager.registry.add_binding(Keys.Tab)
  def tab_handler(event):
    buffer = event.current_buffer
    document = buffer.document
    if buffer.auto_suggest:
      suggestion = buffer.auto_suggest.get_suggestion(event.cli, buffer, document)
      if suggestion.text:
        buffer.text+=suggestion.text
        buffer.cursor_position+=len(suggestion.text)

  style = style_from_pygments(get_style_by_name(env.get(
      '_debug_read_color_scheme', 'vim')))

  try:
    text = prompt(env.get('_debug_prompt', '$ '),
                  lexer=PygmentsLexer(BashLexer),
                  style=style,
                  key_bindings_registry=manager.registry,
                  history=FileHistory(env.get('JUST_DEBUG_HISTORY',
                              os.path.expanduser('~/.debug_bash_history'))+'3'),
                  multiline=True,
                  auto_suggest=AutoSuggestFromHistory())
    sys.stderr.write(text)
  except KeyboardInterrupt:
    pass