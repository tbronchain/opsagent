'''
Madeira OpsAgent utilities

@author: Thibault BRONCHAIN
'''

# System imports
import logging
import time
import subprocess
import os
import shutil

# Custom imports
from opsagent.exception import ManagerInvalidStatesRepoException


# Defines
DEBUG_DELAY=0.1
DEBUG=10
COLOR=True

# Logging defines
LOGGING_EQ = {
    "DEBUG"    : logging.debug,
    "INFO"     : logging.info,
    "WARNING"  : logging.warning,
    "ERROR"    : logging.error,
    "CRITICAL" : logging.critical,
    }

# Colors defines
COLORS_EQ = {
    "DEBUG"    : ("\x1b[38;5;6m","\x1b[0m"),
    "INFO"     : ("\x1b[38;5;15m","\x1b[0m"),
    "WARNING"  : ("\x1b[38;5;3m","\x1b[0m"),
    "ERROR"    : ("\x1b[38;5;1m","\x1b[0m"),
    "CRITICAL" : ("\x1b[38;5;1m","\x1b[0m"),
    }


# Custom logging
def log(action, content, fc=None):
    out = ""
    if logging.getLogger().getEffectiveLevel() == DEBUG:
        time.sleep(DEBUG_DELAY)
    if fc and logging.getLogger().getEffectiveLevel() == DEBUG:
        (f,c) = fc
        c = (c.__class__.__name__ if ((type(c) is not str) and c) else c)
        out += ("%s.%s(): "%(c,f)
                if c
                else "%s(): "%(f))
    pt = ("%s%s"%(out,content)
          if not COLOR
          else "%s%s%s%s"%(COLORS_EQ[action][0],out,content,COLORS_EQ[action][1]))
    LOGGING_EQ[action](pt)

# clone a git repository
def clone_repo(config, path, name, uri):
    try:
        try:
            shutil.rmtree(os.path.normpath(path+'/'+name))
        except Exception as e:
            log("DEBUG", "Exception while removing directory %s: %s"%(os.path.normpath(path+'/'+name),e),('clone_repo','utils'))
        r = subprocess.check_output(("git clone %s %s"%(uri,name)).split(),cwd=path)
        log("INFO", "repo %s from %s successfully cloned in %s: %s"%(name,uri,path,r),('clone_repo','utils'))
        try:
            os.unlink(os.path.normpath(config['global']['package_path']+'/'+config['module']['name']))
        except Exception as e:
            log("DEBUG", "Exception while unlinking %s: %s"%(os.path.normpath(config['global']['package_path']+'/'+config['module']['name']),e),('clone_repo','utils'))
        os.symlink(os.path.normpath(path+'/'+name+'/'+config['module']['src_salt']),os.path.normpath(config['global']['package_path']+'/'+config['module']['name']))
        try:
            os.unlink(os.path.normpath(config['global']['package_path']+'/'+config['module']['dst_adaptor']))
        except Exception as e:
            log("DEBUG", "Exception while unlinking %s: %s"%(os.path.normpath(config['global']['package_path']+'/'+config['module']['dst_adaptor']),e),('clone_repo','utils'))
        os.symlink(os.path.normpath(path+'/'+name+'/'+config['module']['src_adaptor']),os.path.normpath(config['global']['package_path']+'/'+config['module']['dst_adaptor']))
    except Exception as e:
        log("ERROR", "Can't clone %s repo from %s: %s"%(name,uri,e),('clone_repo','utils'))
        raise ManagerInvalidStatesRepoException
    return True

# clone a git branch/tag
def checkout_repo(config, path, name, tag, uri, n=0):
    commands = [
        "git checkout master",
        "git pull",
        "git checkout %s"%(tag),
        ]
    spath = os.path.normpath(path+'/'+name)
    for cmd in commands:
        try:
            r = subprocess.check_output(cmd.split(),cwd=spath)
            log("INFO", "Command succeed %s: %s"%(cmd,r),('checkout_repo','utils'))
        except Exception as e:
            log("WARNING", "Can't update %s repo on %s tag: %s"%(name,tag,e),('checkout_repo','utils'))
            clone_repo(config, path, name, uri)
            if n == 0:
                checkout_repo(config, path, name, tag, uri, n+1)
            else:
                log("ERROR", "Can't switch to requested tag after cloning clean repo, aborting.",('checkout_repo','utils'))
                raise ManagerInvalidStatesRepoException
            break
    if n == 0:
        log("INFO", "Repo %s in %s successfully checkout at %s tag."%(name,spath,tag),('checkout_repo','utils'))
