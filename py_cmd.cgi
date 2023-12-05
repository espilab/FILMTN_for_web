#!/usr/local/bin/python3

import urllib.request
import os
import sys, io
import subprocess
import datetime
import base64
import cgi
import cgitb
cgitb.enable()

py_cmd_version = 'ver 0.1'

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# HTTPヘッダを出力します
print("Content-Type: text/html; charset=utf-8")
print()


### ------ for debug logging file output
fname_log = 'log_data.txt'
log_file_max_size = 19000
fname_log_save = 'log_data@.txt'

def sys_log(log_str):
  global fh_log
  #fh_log.write(log_str+"\n")
  fh_log.write(log_str)
  fh_log.write("\n")
  fh_log.flush()











# get directory entries 
#  return: [ [ filename, size_str, size, mod_time, file_path, is_dir, is_file, file_info], ... ]
#
def get_dir_entry(path, kind, order):
  all_entry_list = []
  #all_entry_list.append(os.path.join(path, '..'))
  sys_log('(path,kind,order)=' + path + ',' + kind + ',' + order)  #DEBUG

  filelist = os.scandir(path)
  for item in filelist:
    name = item.name
    file_path = item.path
    isdir = item.is_dir()
    isfile = item.is_file()
    info = item.stat()
    permissions = 0
    if isdir:
      sizestr = '[DIR]'
    else:
      sizestr = info.st_size
    permissions = info.st_mode & 0o777
    mtime = datetime.datetime.fromtimestamp(info.st_mtime)
    mtime_str = mtime.strftime("%Y-%m-%d %H:%M:%S")
    entry_list = [name, sizestr, info.st_size, mtime_str, mtime, permissions, file_path, isdir, isfile, info]
    all_entry_list.append(entry_list)

  order_bool = True   # default -> up
  if order == 'down':
    order_bool = False
  if kind == 'name':
    sort_dir_list(all_entry_list, 0, order_bool)
  if kind == 'size':
    sort_dir_list(all_entry_list, 2, order_bool)
  if kind == 'date':
    sort_dir_list(all_entry_list, 4, order_bool)

  return all_entry_list


# sort dir.entry list
def sort_dir_list(dir_entry_list, key_no, up_down):
    if up_down:
      dir_entry_list.sort(key=lambda x: x[key_no])
    else:
      dir_entry_list.sort(key=lambda x: x[key_no], reverse=True)



# get file attribute of the one file
def get_file_attr(path, search_fname):
  all_entry_list = get_dir_entry(path, '', '')
  for item in all_entry_list:
    (fname, *_) = item
    if fname == search_fname:
      sys_log(search_fname + ' found ->' + fname)   #DEBUG
      return item
  sys_log(search_fname + ' not found')   #DEBUG
  return ('','0',0,'','','','','')     # not found

# check log file, if size exceeded, move , finally close.
def check_logfile_and_close():
  global log_file_max_size, fname_log, fname_log_save, fh_log
  sys_log('check logfile size')
  (fname, size_str, size, mtime_str, mtime, permissions, file_path, *_) = get_file_attr('./',fname_log)
  if size > log_file_max_size:
    #fh_log.close() 
    (fname, size_str, size, mtime_str, mtime, permissions, file_path, *_) = get_file_attr('./','var')
    if file_path == './var':
      sys_log('./var found')
    else:
      sys_log('./var not found')
      cmd = 'mkdir var' 
      ret = subprocess.call(cmd, shell=True)
      if ret == 0:
        sys_log('mkdir var id ok.')
      else: 
        sys_log('mkdir var failed.')
    datestr = (datetime.datetime.now()).strftime('%Y%m%d_%H%M%S')
    sys_log('log file size exceeded, move to var/* ' + datestr)
    fname_log_back = fname_log_save.replace('@', datestr)
    fh_log.close()
    cmd = 'mv ' + fname_log + ' var/' + fname_log_back
    ret = subprocess.call(cmd, shell=True)
    #cmd = 'rm -f ' + fname_log
    #ret = subprocess.call(cmd, shell=True)
  else:
    sys_log('log file size=' + str(size) + ' (limit=' + str(log_file_max_size) + ')')
    sys_log('finish')
    fh_log.close()

# convert any date to string
def any2str(input):
    if isinstance(input, list):
        return ', '.join(map(any2str, input))
    elif isinstance(input, str):
        return input
    elif isinstance(input, (int, float)):
        return str(input)
    elif isinstance(input, dict):
        return str(input)
    elif isinstance(input, tuple):
        return ', '.join(map(any2str, input))
    elif input is None:
        return "None"
    elif isinstance(input, bytes):
        return input.decode('utf-8')
    else:
        return "Error: Input must be a list, a string, a number, a dictionary, a tuple, a bytes object, or None."



#------------------------ main ------------------------------ 
# fh_log is global var.
fh_log = open(fname_log, 'a', encoding='utf-8')
#fh_log = open(fname_log, 'ab')
#os.chmod(fname_log, 0o666)   #error on sakura server 
now_str = (datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
sys_log('#### Log_start:' + now_str)

#exit(1) #DEBUG

#cmd = 'dir'   #DEBUG

form = cgi.FieldStorage()
#sys_log(form) 

# ------ pick-up parameters from javascrpt request(ajax)
if "cmd" in form:
  cmd = form.getvalue('cmd')
  print('cmd=', cmd, sep="")
  sys_log('cmd=' + any2str(cmd))
  #exit(1)
else:
  sys_log('cmd  not exist in form,  let cmd=dir')
  print('cmd not exist in form')
  cmd='dir'

path = '.'
sys_log('temporary,path=' + path)

if "param1" in form:
  param1 = form.getvalue('param1')
  sys_log('param1=' + any2str(param1)) 
else:
  if cmd == 'dir':
    param1 = './'
  else:
    param1 = ''
  sys_log('param1=(null) ->' + param1)

#param1 = './'   #DEBUG

if "param2" in form:
  param2 = form.getvalue('param2')
  #sys_log('param2=' + any2str(param2))
else:
  param2 = ''
  sys_log('param2=(null)')


# ----------------------- process each command 
if cmd == 'dir':
  path = param1
  if "=" in param2:
    (sort_kind, sort_order) = param2.split('=')
  else:
    sort_kind = ''
    sort_order = ''
  filelist = get_dir_entry(path, sort_kind, sort_order)   # (path, sort_kind, sort_order) 
  for item in filelist:
    (fname, size_str, size, mtime_str, mtime, permissions, file_path, is_dir, is_file, file_info) = item
    print(fname, ',', size_str, ',', mtime_str, ',', permissions, ',', file_path, ',', is_dir, ',', is_file, sep="")
    #sys_log('fname='+fname)

if cmd == 'cre_file':
  fname = param1
  f = open(fname, 'w')
  f.write('')
  f.close()
  print('new file:', fname)

if cmd == 'make_dir':
  cmd = 'mkdir ' + param1 
  ret = subprocess.call(cmd, shell=True)
  sys_log('mkdir, cmd=' + cmd + ' ret=' + str(ret) )
  if (ret != 0):
    print('Error') 
  print('mkdir result=',ret)

if cmd == 'rm_dir':
  cmd = 'rmdir ' + param1 
  ret = subprocess.call(cmd, shell=True)
  sys_log('rmdir, cmd=' + cmd + ' ret=' + str(ret) )
  if (ret != 0):
    print('Error') 
  print('rmdir result=',ret)

if cmd == 'copy_to':
  (from_fname, to_fname) = (form.getvalue('param1')).split(',')
  cmd = 'cp ' + from_fname + ' ' + to_fname
  ret = subprocess.call(cmd, shell=True)
  if (ret != 0):
    print('Error') 
  sys_log('copy_to, cmd=' + cmd + ' ret=' + str(ret) )
  print('copy result=',ret)

if cmd == 'move_to':
  from_fname = '"' + urllib.parse.unquote(param1) + '"' 
  to_fname = param2
  cmd = 'mv ' + from_fname + ' ' + to_fname
  ret = subprocess.call(cmd, shell=True)
  if (ret != 0):
    print('Error') 
  sys_log('move_to, cmd=' + cmd + ' ret=' + str(ret) )
  print('move result=',ret)




if cmd == 'del_file':
  fname = '"' + urllib.parse.unquote(param1) + '"'
  cmd = 'rm -f ' + fname
  ret = subprocess.call(cmd, shell=True)
  if (ret != 0):
    print('Error') 
  print('delete result=',ret)
  
if cmd == 'chmod_file':
  (fname, mode_str) = (form.getvalue('param1')).split(',')
  cmd = 'chmod ' + mode_str + ' ' + fname
  ret = subprocess.call(cmd, shell=True)
  if (ret != 0):
    print('Error') 
  sys_log('chmod, cmd=' + cmd + ' ret=' + str(ret) )
  print('chmod result=',ret)

if cmd == 'get_file':
  fname = param1
  with open(fname, 'r', encoding='utf-8') as f:
    content = f.read()
  print(fname)      # return (insert) the file name into 2nd line 
  print(content, end="", sep="")


if cmd == 'get_ver':
  print(py_cmd_version)   # return version
  sys_log('version =' + py_cmd_version) 


# ------- save text file
if cmd == 'save_text_file':
  fname = param1
  content_enc = param2
  # デコード
  content = urllib.parse.unquote(content_enc)
  #content = base64.b64decode(content_enc)
  
  sys_log('save, fname=' + any2str(fname))
  sys_log('content=')
  sys_log(content)
  sys_log("///(END of content)\n")

  try:
    file = open(fname, 'w', encoding='utf-8') 
    file.write(content)
  except:
    print('Error')
    print('An error occurred while writing to the file:', fname)
    sys_log('An error occurred while writing to the file:' + fname)
  else:
    print('The file:', fname, ' was written successfully.', sep="")
  #finally:
    file.close()
  #print('save, fname="',fname, '"', sep="")


# ------- save binary file
if cmd == 'save_bin_file':
  fname = param1
  content_enc = param2
  # デコード
  content_bin = base64.b64decode(urllib.parse.unquote(content_enc))
  #content = base64.b64decode(content_enc)
  
  sys_log('save bin, fname=' + any2str(fname))
  sys_log('content=(omit)')
  #sys_log(content)
  sys_log("///(END of content)\n")

  try:
    file = open(fname, 'wb') 
    file.write(content_bin)
  except:
    print('Error')
    print('An error occurred while writing to the file:', fname)
  else:
    print('The file:', fname, ' was written successfully.', sep="")
  #finally:
    file.close()
  #print('save, fname="',fname, '"', sep="")



# ------- execute caommand
if cmd == 'exec_cmd':
  cmd_line = param1
  ret = subprocess.call(cmd_line, shell=True)
  if (ret != 0):
    print('Error') 
  print('exec cmd result=',ret)
  sys_log('exec cmd, cmd_line=' + cmd_line + ', ret=' + any2str(ret))


# check log file size, remove if the size exceeded.
check_logfile_and_close()
#fh_log.close()  #DEBUG
