import sys
import os
import threading
import logging

from vsi.tools.python import Try

class RedirectBase(object):
  def flush(self):
    ''' Flushes stdout and stderr '''
    sys.stdout.flush()
    sys.stderr.flush()  

class Logger(object):
  ''' File object wrapper for logger.
  
      Careful when using this, if the logging out goes to a stream that is 
      redireted, you have an infinite capture loop and does not go well
      
      Use PopenRediret instead of Redirect in that case'''
  def __init__(self, logger, lvl=logging.INFO):
    ''' Create a wrapper for logger using lvl level '''

    self.logger=logger
    self.lvl = lvl
  
  def write(self, str):
    ''' Write method '''
    str = str.rstrip()
    if str:
      self.logger.log(self.lvl, str)

class FileRedirect(object):
  ''' Redirect a real file object to any object with .write

      Some function need a REAL file object with file number and all. This
      class wraps a pair of pipes per output and so what everytime the pipe
      is written to, output.write is called.
  
      Only supports one way communication. You can write to the file object 
      via any valid call, and the other end of the pipe performs "readlines"
      and calls output.write() It would be possible to expand this to two way,
      but not currently needed.
      
      Primarily used in a with expresstion:
      
      >>> from StringIO import StringIO
      >>> s = StringIO()
      >>> with FileRedirect([s]) as f:
      >>>   f.wids[0].write('hiya')
      >>> s.seek(0); print s.read()
      
      IF you call __enter__ manually, you only need to close the wids file
      objects, and the rest of the threads and file objects are cleaned up,
      of course it would be better to call __exit__ in that case.
      '''
  def __init__(self, outputs=[]):
    ''' Create a FileRedirect
    
        outputs - list of outputs objects to write to. For every output in 
                  outputs, an rid in self.rids and wid in self.wids is created
                  when call with with '''
    self.outputs = outputs

  def __enter__(self):
    ''' Create the pipes and monitoring threads '''
    self.rids = []
    self.wids = []
    self.tids = [];
    
    for index, output in enumerate(self.outputs):
      r, w = os.pipe()
      self.rids.append(os.fdopen(r, 'rb'))
      self.wids.append(os.fdopen(w, 'wb'))
      
      self.startMonitor(index)
    
    return self
  
  def __exit__(self, exc_type=None, exc_value=None, traceback=None):
    ''' Closes the write ends of the pipes, and join with monitoring threads
    
        The read pipes are automatically closed by the monitors'''
    for wid in self.wids:
      wid.close()
      
    for tid in self.tids:
      tid.join()

  def __bleed(self, streamIndex):
    ''' Function to read all the data and write to output
     
        Automactically closes read pipe when done. Can only be stopped by
        closing the write end of pipe.'''
    rid = self.rids[streamIndex]
    wid = self.wids[streamIndex]
    output = self.outputs[streamIndex]

    #do-while
    chunk = True
    while chunk: #while rid isn't closed
      chunk = rid.readline(64*1024) #read a chunk
      output.write(chunk) #write chunk
    rid.close()

  def startMonitor(self, stream_index):
    ''' Start a new thread to monitor the stream
    
        Should only be called once per stream_index'''
    self.tids.append(threading.Thread(target=self.__bleed, args=(stream_index,)))
    self.tids[-1].start()

class PopenRedirect(FileRedirect):
  ''' Version FileRedirect object geared towards redirecting for Popen commands
  
      >>> from StringIO import StringIO
      >>> from subprocess import Popen
      >>> out = StringIO(); err = StringIO()
      >>> with PopenRedirect(out, err) as f:
      >>>   Popen(['whoami'], stdout=f.stdout, stderr=f.stderr).wait()
      >>>   Popen(['whoami', 'non user'], stdout=f.stdout, stderr=f.stderr).wait()
      >>> out.seek(0); err.seek(0)
      >>> print out.read(), err.read()
  '''
  def __init__(self, stdout=type('Foo', (object,), {'write':lambda x,y:None})(),
                     stderr=type('Bar', (object,), {'write':lambda x,y:None})()):
    ''' Create PopenRedirect object  
    
        Parameters:
        stdout - Stdout File like object, must have .write method
        stderr - Stderr File like object, must have .write method
        
        
        '''
    self.stdout_output = stdout
    self.stderr_output = stderr
    
    super(PopenRedirect, self).__init__([stdout, stderr])

  @property
  def stdout(self):
    return self.wids[0]

  @property
  def stderr(self):
    return self.wids[1]

class Redirect(RedirectBase): #Version 2
  ''' Similar to Capture class, except it redirect to file like objects
  
      There are times in python when using "those kind of libraries" 
      where you have to capture either stdout or stderr, and many 
      situations are tricky. This class will help you, by using a with
      statement.

      from StringIO import StringIO
      stdout = StringIO()
      with Redirect(stdout=stdout):
        some_library.call157()

      stdout.seek(0,0)
      print stdout.read()

      There are 4 output pipe of concern, none of which are synced with
      each other (flushed together).

      stdout and stderr from c (referred to as stdout_c, stderr_c) and
      stdout and stderr from python (referred to as stdout_py, stderr_py).

      Most python functions use the python stdout/stderr, controlled by
      sys.stdout and sys.stderr. However c embedded calls are used the 
      c stdout/stderr, usually fd 1 and 2. Because of this, there are 4
      streams to consider'''

  def __init__(self, 
               all=None,
               stdout=None,
               stderr=None,
               c=None, py=None,
               stdout_c=None, stderr_c=None, 
               stdout_py=None, stderr_py=None,
               stdout_c_fd=1, stderr_c_fd=2, 
               stdout_py_module=sys,    stderr_py_module=sys,
               stdout_py_name='stdout', stderr_py_name='stderr'):
    ''' Create the Redirect object

        Optional Arguments: File Output Argument. All File output arguments 
          should use File like Python objects that have a .write call.
          Many of the argument override the other argument for ease of use
        
        all - Output stdout_c, stderr_c, stdout_py and stderr_py to the
              all file.
        stdout - Output stdout_c and stdout_py to the stdout file.
        stderr - Output stderr_c and stderr_py to the stderr file.
        c - Output stdout_c and stderr_c to the c file.
        py - Output stdout_py and stderr_py to the py file.
        stdout_c, stderr_c, stdout_py, stderr_py - Output to each 
              individual stream for maximum customization.
        
        Other Optional Arguments:
        
        stdout_c_fd, stderr_c_fd - The default file number used for
              stdout (1) and stderr (2). There should be no reason to 
              override this
        stdout_module, stderr_module
        stdout_name, stderr_name - Because of the nature of python, in 
              order to replace and restore the python object, the module
              and name of attribute must be passed through, where name is a
              string and module and the acutal module. The default is sys
              module and "stdout" or "stderr" (Including the quotes). Again,
              there should be no real reason to override these, unless you are
              doing some IPython/colorama redirecting, or any other library 
              that messes with sys.stdout/sys.stderr
              ''' 
    #copy original file informatio
    self.stdout_c_fd=stdout_c_fd
    self.stderr_c_fd=stderr_c_fd
    self.stdout_py_module=stdout_py_module
    self.stdout_py_name=stdout_py_name
    self.stderr_py_module=stderr_py_module
    self.stderr_py_name=stderr_py_name

    #Determine the "who gets router who" pattern
    self.stdout_c_out = stdout_c
    self.stderr_c_out = stderr_c
    self.stdout_py_out = stdout_py
    self.stderr_py_out = stderr_py

    if c is not None:
      self.stdout_c_out = c
      self.stderr_c_out = c
    
    if py is not None:
      self.stdout_py_out = py
      self.stderr_py_out = py
    
    if stdout is not None:
      self.stdout_c_out = stdout
      self.stdout_py_out = stdout

    if stderr is not None:
      self.stderr_c_out = stderr
      self.stderr_py_out = stderr

    if all is not None:
      self.stdout_c_out = all
      self.stderr_c_out = all
      self.stdout_py_out = all
      self.stderr_py_out = all

    #Determine output set
    outputs = set((self.stdout_c_out, 
                   self.stderr_c_out, 
                   self.stdout_py_out, 
                   self.stderr_py_out))
    with Try(KeyError):
      outputs.remove(None)
    #Now output contains a unique list of outputs, not including None
    
    self.inputs_c = []
    self.inputs_py_module = []
    self.inputs_py_name = []
    self.outputs = []
    
    #Map out inputs and outputs
    for output in outputs:
      self.inputs_c.append([])
      self.inputs_py_module.append([])
      self.inputs_py_name.append([])
      self.outputs.append(output)
      
      if self.stdout_c_out == output:
        self.inputs_c[-1].append(self.stdout_c_fd)
      if self.stderr_c_out == output:
        self.inputs_c[-1].append(self.stderr_c_fd)
      if self.stdout_py_out == output:
        self.inputs_py_module[-1].append(self.stdout_py_module)
        self.inputs_py_name[-1].append(self.stdout_py_name)
      if self.stderr_py_out == output:
        self.inputs_py_module[-1].append(self.stderr_py_module)
        self.inputs_py_name[-1].append(self.stderr_py_name)
    
    super(Redirect, self).__init__();

  def __enter__(self):
    ''' enter function for with statement. 

        Switched out stderr and stdout, and starts pipe threads'''

    #Clear initial arrays
    self.tids = [] #List of threads running __bleed
    self.writer_fids = [] # list of file objects for the write_pipes

    #Flush
    self.flush()
    
    self.copies_c = []
    self.copies_py = []
    for output,inputs_c, inputs_py_module, inputs_py_name in zip(self.outputs, self.inputs_c, self.inputs_py_module, self.inputs_py_name):
      #Create the paired pipes
      (reader,writer_c) = os.pipe()
      writer_fid = os.fdopen(writer_c, 'wb')
      self.writer_fids.append(writer_fid)
      #To assist in cleanup in __exit__
      
      self.startMonitor(reader, output)
      
      self.copies_c.append([])
      for input_c in inputs_c:
        self.copies_c[-1].append(os.dup(input_c))
        #Copy for recover in __exit__
        os.dup2(writer_c, input_c)
        #Replace the fd with the pipe
        
      self.copies_py.append([])
      for input_module, input_name in zip(inputs_py_module, inputs_py_name):
        self.copies_py[-1].append(getattr(input_module, input_name))
         #Copy for recover in __exit__
        setattr(input_module, input_name, writer_fid)
        #Replace the File with the pipe File object

    return self

  def __exit__(self, exc_type=None, exc_value=None, traceback=None):
    ''' exit function for with statement. 

        Restores stdout and sterr, closes write pipe and joins with the 
        threads'''
    #Flush
    self.flush()

    for writer_fid, inputs_c, inputs_py_module, inputs_py_name, copies_c, copies_py in zip(self.writer_fids, self.inputs_c, self.inputs_py_module, self.inputs_py_name, self.copies_c, self.copies_py):
      writer_fid.close()
      
      for input_module, input_name, copy_py in reversed(zip(inputs_py_module, inputs_py_name, copies_py)):
        setattr(input_module, input_name, copy_py)
      
      for input_c, copy_c in reversed(zip(inputs_c, copies_c)):
        os.dup2(copy_c, input_c)


    for copy_c in set(sum(self.copies_c, [])):
      os.close(copy_c)

    for tid in self.tids:
      tid.join()
      
  def startMonitor(self, readPipe, output):
    self.tids.append(threading.Thread(target=self.__bleed, args=(readPipe, output)))
    self.tids[-1].start()

  def __bleed(self, fid, output):
    chunk = True
    
    fid_py = os.fdopen(fid)

    while chunk: #while fid isn't closed
      chunk = fid_py.readline(64*1024) #read a chunk
      #chunk = fid_py.read(64*1024) #read a chunk
      #chunk = os.read(fid, 64*1024) #read a chunk
      output.write(chunk) #write chunk
    
    fid_py.close()
    #os.close(fid) #Clean up those fids now


class Capture(RedirectBase): #version 1
  ''' A class to easily redirect stdout and stderr to a sting buffer

      There are times in python when using "those kind of libraries" 
      where you have to capture either stdout or stderr, and many 
      situations are tricky. This class will help you, by using a with
      statement.

      with Redirect() as rid:
        some_library.call157()

      print rid.stdout

      There are 4 output pipe of concern, none of which are synced with
      each other (flushed together).

      stdout and stderr from c (referred to as stdout_c, stderr_c) and
      stdout and stderr from python (referred to as stdout_py, stderr_py).

      Most python functions use the python stdout/stderr, controlled by
      sys.stdout and sys.stderr. However c embedded calls are used the 
      c stdout/stderr, usually fd 1 and 2. Because of this, there are 4
      streams to consider
      
      Once Redirect is done, the results are store in
      >>> self.stdout_c - Standard out output for c
      >>> self.stderr_c - Standard error output for c
      >>> self.stdout_py - Standard out output for python
      >>> self.stderr_py - Standard error output for python
      
      When the streams are grouped, they both contain the same data.
      In the group_out and group_err case, an addtion attribute is defined
      >>> self.stdout - Standard out output
      >>> self.stderr - Standard error output 
      Just to make it easier
  
  
      If you want a more complicated scenario, say you want stdout_c and
      stderr_py grouped, and stderr_c and stdout_py groups because you've
      been drinking too much. Well, this is easy to do by calling Redirect
      twice:
      
      with Redirect(stdout_c=None, stderr_py=None) as rid1:
        with Redirect(stderr_c=None, stdout_py=None) as rid2:
          stuff()
          
      Now rid1's buffer has just stderr_c and stdout_py as one group 
      stream and rid2 has stfout_c and stderr_py as one grouped stream'''

  def __init__(self, stdout_c=1, stderr_c=2, 
                     stdout_py=sys.stdout, stderr_py=sys.stderr, 
                     group=True,
                     group_outerr=True, group_out=True, group_err=True):
    ''' Initialize the Redirect object

        Optional Arguments:
        stdout_c - The fd to be replace, usually 1 will work, but change it 
                   in case this is not right in your case (default: 1)
                   None means to not redirect
        stderr_c - The fd to be replaced, usually 2 will work, but change it 
                   in case this is not right in your case (default: 2)
                   None means to not redirect
        stdout_py - The file object to be replaced (default: sys.stdout)
                    None means to not redirect
        stderr_py - The file object to be replaced (default: sys.stderr)
                    None means to not redirect
        group - Should ANY of the stream be joined together. This 
                overrides ALL of the following group options 
        group_outerr - Should stdout and stderr use the a group stream or
                       else it will have separate streams (default: True)
        group_out - Should stdout_c and stdout_py use the a group stream or
                    else it will have separate streams (default: True)
        group_err - Should stderr_c and stderr_py use the a group stream or
                    else it will have separate streams (default: True)'''
    self.stdout_c_fd=stdout_c
    self.stderr_c_fd=stderr_c
    self.stdout_py_fid=stdout_py
    self.stderr_py_fid=stderr_py
    self.group_outerr=group_outerr
    self.group_out=group_out
    self.group_err=group_err

    if not group:
      self.group_outerr=False
      self.group_out=False
      self.group_err=False

    if self.group_outerr and (self.group_out or self.group_err): #that's an or, not an and
      #Basically if two of the group are True, All 4 go through one stream
      #I can't see wanting 3 and not the 4th separate.
      self.group_all = True
    else:
      self.group_all = False
      
    #Redirect scenarios
    self.std_cs = [] #list of lists of strings for the c outs associates with the pipes
    self.std_pys = [] #list of lists of strings for the python outs associates with the pipes
    
    # This fun piece of code sets up the "Redirect scenarios"
    if self.group_all:
      #add all together
      self.std_cs.append(['stdout', 'stderr'])
      self.std_pys.append(['stdout', 'stderr'])
    else:
      if self.group_out:
        #add stdouts together
        self.std_cs.append(['stdout'])
        self.std_pys.append(['stdout'])                         
      else:
        #add stdout_c
        self.std_cs.append(['stdout'])
        self.std_pys.append([])
        #add stdout_py
        self.std_cs.append([])
        self.std_pys.append(['stdout'])                         
      if self.group_err:
        #add stderrs together
        self.std_cs.append(['stderr'])
        self.std_pys.append(['stderr'])                         
      else:
        #add stderr_c
        self.std_cs.append(['stderr'])
        self.std_pys.append([])
        #add stderr_py
        self.std_cs.append([])
        self.std_pys.append(['stderr'])
        
    self.buffers = [''] * len(self.std_cs)
    
    super(Capture, self).__init__();
    
  def __bleed(self, fid, bufferIndex):
    ''' Read all date from fid and store in buffer[bufferIndex]
    
        This function reads large chuncks at a time (for efficientcy and then
        appends them to the appropriate bufffer. When the write pipe is closed,
        the loop will end and then close the read pipe '''

    chunk = True

    while chunk: #while fid isn't closed
      chunk = os.read(fid, 64*1024) #read a chunk
      self.buffers[bufferIndex] += chunk #add to the buffer
    os.close(fid) #Clearn up those fids now
  

  def startMonitor(self, readPipe, bufferIndex):
    ''' Start a read pipe monitoring thread
    
        Runs __bleed in a background thread to capture all the redirected 
        output and stores the information in the self.buffers[bufferIndex].
        
        Appends the thread object to self.tids

        Arguments:
        readPipe - File descriptor number of the read pipe (from by os.pipe)
        bufferIndex - The xth buffer to store the string in. '''
    self.tids.append(threading.Thread(target=self.__bleed, args=(readPipe, bufferIndex)))
    self.tids[-1].start()


  def __enter__(self):
    ''' enter function for with statement. 

        Switched out stderr and stdout, and starts pipe threads'''

    #Clear initial arrays
    self.tids = [] #List of threads running __bleed
    self.read_pipes = [] #list of read pipes
    self.write_pipes = [] #list of write pipes
    self.write_fids = [] # list of file objects for the write_pipes

    #Flush
    self.flush()

    #Copy of fds/handles to put back
    if self.stdout_c_fd is not None:
      self.stdout_c_copy = os.dup(self.stdout_c_fd)
    if self.stderr_c_fd is not None:
      self.stderr_c_copy = os.dup(self.stderr_c_fd)
    #self.copied = os.fdopen(os.dup(self.stdout_fd), 'wb') #Copy of stdout handle to put back

    for x in range(len(self.std_cs)):
      #Create the paired pipes
      (r,w) = os.pipe()
      self.read_pipes.append(r)
      self.write_pipes.append(w)
      self.write_fids.append(os.fdopen(w, 'wb'))

      self.startMonitor(r, len(self.read_pipes)-1)

      for std in self.std_cs[x]:
        if getattr(self, std+'_c_fd') is not None: #self.stdxxx_c_fd is not None
          #Replace the c fd with the write pipe
          os.dup2(w, getattr(self, std+'_c_fd'))
      for std in self.std_pys[x]:
        if getattr(self, std+'_py_fid') is not None: #self.stdxxx_py_fid is not None
          setattr(sys, std, self.write_fids[x])

    return self


  def __exit__(self, exc_type=None, exc_value=None, traceback=None):
    ''' exit function for with statement. 

        Restores stdout and sterr, closes write pipe and joins with the 
        threads'''
    #Flush
    self.flush()

    for x in range(len(self.std_cs)):
      self.write_fids[x].close()
      for std in self.std_pys[x]:
        if getattr(self, std+'_py_fid') is not None: #self.stdxxx_py_fid is not None
          #sys.stdxxx = self.stdxxx_py_fid
          setattr(sys, std, getattr(self, std+'_py_fid'))
      for std in self.std_cs[x]:
        if getattr(self, std+'_c_fd') is not None: #self.stdxxx_c_fd is not None
          #Restore stdxxx to original fd
          os.dup2(getattr(self, std+'_c_copy'), #self.stdxxx_c_copy
                  getattr(self, std+'_c_fd'))      #self.stdxxx_c
    # Close the copy now
    if self.stdout_c_fd is not None:
      os.close(self.stdout_c_copy)
    if self.stderr_c_fd is not None:
      os.close(self.stderr_c_copy)

    for tid in self.tids:
      tid.join()
    
    self.__renameBuffer()
      
  def __renameBuffer(self):
    ''' Take the buffers and store them in common names
    
        Instead of accessing self.buffers, the strings are copied to common 
        names, including stdout_c, stderr_c, stdout_py, stdout_py. If 
        group_out/group_err is True, then stdout/stderr is defines
        (respectively) just to make it easier'''
    for x in range(len(self.std_cs)):
      for std in self.std_cs[x]:
        setattr(self, std+'_c', self.buffers[x])
      for std in self.std_pys[x]:
        setattr(self, std+'_py', self.buffers[x])
    #Easier names just to make life easier
    if self.group_out:
      self.stdout = self.stdout_c
    if self.group_err:
      self.stderr = self.stderr_c
      
if __name__=='__main__':
  with Redirect(group=False) as rid:
    RedirectTest._RedirectTest__simple()
  print 'Stdout_c:', rid.stdout_c,
  print 'Stderr_c:', rid.stderr_c,
  print 'Stdout_py:', rid.stdout_py,
  print 'Stderr_py:', rid.stderr_py,
  