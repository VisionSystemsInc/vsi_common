import urllib2
import Cookie

from StringIO import StringIO
import zlib

def authorizeBasic(user=None, password=None, realm=None, uri=None):
  #This was needed. But not anymore
  if user and password and realm and uri:
    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm=realm, uri=uri, user=user, passwd=password)
    opener = urllib2.build_opener(auth_handler)
    urllib2.install_opener(opener)

def _makeCookieString(cookie):
  simpleCookie = Cookie.SimpleCookie(cookie)
  cookieString = []
  for morselName in simpleCookie:
    cookieString.append('%s=%s' % (morselName, simpleCookie[morselName].coded_value))
  return '; '.join(cookieString)

def download(url, filename=None, chunkSize=2**20, cookie={}, disableSslCertVerify=False):
  #start simple, add feautres as time evolves
  #cookie - an optional dictionary

  request = urllib2.Request(url);
  request.add_header('Accept-encoding', 'gzip');

  if cookie:
    request.add_header('Cookie', _makeCookieString(cookie))
  
  context=None
  if disableSslCertVerify and url.startswith('https://'):
    import ssl
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1) #disable cert checking

  try:
    response = urllib2.urlopen(request, context=context);
  except: #python pre 2.7
    response = urllib2.urlopen(request);

  if response.info().get('Content-Encoding') == 'gzip':
    gzipped = True;
    decompressor = zlib.decompressobj(16+zlib.MAX_WBITS)
    #Why 16+zlib.MAX_WBITS???
    #http://www.zlib.net/manual.html
    #Basically means gzip for zlib
  else:
    gzipped = False;

  if filename:
    output = open(filename, 'wb')
  else:
    from StringIO import StringIO
    output = StringIO()
    
  buf = True;
  while buf:
    buf = response.read(chunkSize);
    if gzipped:
      output.write(decompressor.decompress(buf))
    else:
      output.write(buf);
  
  if filename:
    output.close()
  else:
    output.seek(0)
    return output.read() 
  
