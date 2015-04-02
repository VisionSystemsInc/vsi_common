from subprocess import Popen, PIPE
import xml.etree.ElementTree as ElementTree
import datetime
import os
import tempfile

class WmicProperty(object):
  def __init__(self, name, type, value=None,perm=None):
    self.name = name
    self.type = type
    self.perm = perm

    if value:
      if self.type=='string':
        self.value = str(value)
      elif self.type in ['uint64', 'uint32', 'uint16']:
        self.value = int(value)
      elif self.type=='datetime':
        self.value = datetime.datetime.strptime(value.strip('"\'')[0:21], '%Y%m%d%H%M%S.%f')
        self.tz = value[21:] #This is in +/-MINUTES only, not +/-hhmm
      else:
        raise Exception('Unknown type %s' % self.type)
    else:
      self.value = None
  
  def __str__(self):
    s = '%s=%s' % (self.name, self.value)
    return s

class Wmic(object):
  def __init__(self, path):
    self.path = path
    
  def help(self):
    pid = Popen(['wmic', 'path', self.path, '/?'], stdout=PIPE, stderr=PIPE)
    (o,e) = pid.communicate()
    pid.wait()
    return o
  
  def getProperties(self):
    pid = Popen(['wmic', 'path', self.path, 'GET', '/?'], stdout=PIPE, stderr=PIPE)
    (o,e) = pid.communicate()
    pid.wait()
    
    o = o.split('\n')
    preheader = next(x for x in range(len(o)) if o[x].startswith('The following properties are available:'))

    props = []    
    for line in o[preheader+3:]:
      line = map(lambda x:x.strip(), line.split())
      if len(line)<3:
        break
      props.append(WmicProperty(name=line[0], type=line[1], perm=line[2]))
    return props
  
  @staticmethod
  def getPaths():
    ''' Get all possible paths'''
    temp = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.vbs')
    temp.write(r'''strComputer = "."
Set objWMIService=GetObject("winmgmts:{impersonationLevel=impersonate}!\\" & strComputer & "\root\cimv2")
For Each objclass in objWMIService.SubclassesOf()
    Wscript.Echo objClass.Path_.Class
Next''')
    temp.close()
    pid = Popen(['cscript', '//Nologo', temp.name], stdout=PIPE, stderr=PIPE)
    (o,e) = pid.communicate()
    pid.wait()
    os.remove(temp.name)
    return filter(lambda x:x, map(lambda x:x.strip(), o.split('\n')))

class Pgrep(object):
  def __init__(self, args=[], get=['/all']):
    self.args = args;
    self.cmd = ['wmic', 'path', 'win32_process']
    self.cmd += args
    self.cmd += ['get', ','.join(get), '/FORMAT:rawxml']
    self.pids = []

    self.run()
    self.parse()

  def run(self):
    pid = Popen(self.cmd, stdout=PIPE, stderr=PIPE)
    (self.rawout, self.rawerr) = pid.communicate()
    self.pid = pid.pid
    pid.wait()
    if not pid.returncode == 0:
      raise Exception('wmic returned %d' % pid.returncode)

  def parse(self):
    self.pids = []
    etree = ElementTree.fromstring(self.rawout) 
    results = etree.find('RESULTS')
    if results is None:
      return
    cim = results.find('CIM')
    if cim is None:
      return
      
    for instance in cim:
      pid = {}
      for property in instance:
        value = property.getchildren() #Speed irrelevant
        if value:
          value = value[0].text
        else:
          value = None
        
        key = property.attrib['NAME'].lower()
        ty = property.attrib['TYPE']
        
        if value is None:
          pid[key] = None
        else:
          if ty=='string':
            pid[key] = str(value)
          elif ty in ['uint64', 'uint32', 'uint16']:
            pid[key] = int(value)
          elif ty=='datetime':
            dt = datetime.datetime.strptime(value.strip('"\'')[0:21], '%Y%m%d%H%M%S.%f')
            pid[key] = (dt, value[21:])
          else:
            raise Exception('Unknown type %s' % ty)
      self.pids.append(pid)
