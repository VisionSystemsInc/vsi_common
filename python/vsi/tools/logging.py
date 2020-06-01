import logging


def show_log(k, v):
  def show_dict_fields(prefix, dict1):
    for fld,val in dict1.items():
      print('%s%s=%s' %(prefix, fld,val) )

  if not isinstance(v, logging.PlaceHolder):
    print('+ [%s] {%s} (%s) ' % (str.ljust( k, 20), str(v.__class__)[8:-2],
                                 logging.getLevelName(v.level)) )
    print(str.ljust( '-------------------------',20) )
    show_dict_fields('   -', v.__dict__)

    for h in v.handlers:
      print('     +++%s (%s)' %(str(h.__class__)[8:-2],
                                logging.getLevelName(h.level) ))
      show_dict_fields('   -', h.__dict__)

# https://github.com/mickeyperlstein/logging_debugger/blob/master/__init__.py
def show_logs_and_handlers():
  show_log('root', logging.getLogger(''))
  for k,v in logging.Logger.manager.loggerDict.items():
    show_log(k,v)
