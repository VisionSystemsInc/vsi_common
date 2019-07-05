try:
  import urllib2
except ImportError:
  import urllib.request as urllib2

try:
  from Cookie import SimpleCookie
except ImportError:
  from http.cookies import SimpleCookie

try:
  from StringIO import StringIO
except ImportError:
  from io import StringIO

import zlib

def authorize_basic(user=None, password=None, realm=None, uri=None):
  ''' Call before calling download

  Parameters
  ----------
  user : str
      The User
  password : str
      The Password
  realm : str
      The Realm
  uri : str
      The Uri

  Returns
  -------
  str
      The filename

  '''
  if user and password and realm and uri:
    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm=realm, uri=uri, user=user, passwd=password)
    opener = urllib2.build_opener(auth_handler)
    urllib2.install_opener(opener)

def _make_cookie_string(cookie):
  simple_cookie = SimpleCookie(cookie)
  cookie_string = []
  for morsel_name in simple_cookie:
    cookie_string.append('%s=%s' % (morsel_name, simple_sookie[morsel_name].coded_value))
  return '; '.join(cookie_string)

def download(url, filename=None, chunk_size=2**20, cookie={}, disable_ssl_verify=False):
  #start simple, add feautres as time evolves
  #cookie - an optional dictionary

  request = urllib2.Request(url)
  request.add_header('Accept-encoding', 'gzip')

  if cookie:
    request.add_header('Cookie', _make_cookie_string(cookie))

  context=None
  if disable_ssl_verify and url.startswith('https://'):
    import ssl
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1) #disable cert checking

  try:
    response = urllib2.urlopen(request, context=context)
  except: #python pre 2.7
    response = urllib2.urlopen(request)

  if response.info().get('Content-Encoding') == 'gzip':
    gzipped = True
    decompressor = zlib.decompressobj(16+zlib.MAX_WBITS)
    #Why 16+zlib.MAX_WBITS???
    #http://www.zlib.net/manual.html
    #Basically means gzip for zlib
  else:
    gzipped = False

  if filename:
    output = open(filename, 'wb')
  else:
    from StringIO import StringIO
    output = StringIO()

  buf = True
  while buf:
    buf = response.read(chunk_size)
    if gzipped:
      output.write(decompressor.decompress(buf))
    else:
      output.write(buf)

  if filename:
    output.close()
  else:
    output.seek(0)
    return output.read()
