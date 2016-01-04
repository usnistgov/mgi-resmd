"""
xjs submodule tests
"""
import os, shutil

tmpname = "_test"

def ensure_tmpdir(basedir=None, dirname=None):
    """
    ensure the existance of a directory where temporary inputs and outputs 
    can be placed.  This directory is not cleaned up after use.  

    :argument str basedir: the desired path to tmp directory's parent directory.
                           if not provided, the directory will be placed in the 
                           current working directory.
    :return str: the path to the temporary directory
    """
    tdir = tmpdir(basedir, dirname)
    if not os.path.isdir(tdir):
        os.mkdir(tdir)

    return tdir

def tmpdir(basedir=None, dirname=None):
    """
    return the name of a temporary directory where temporary inputs and outputs 
    can be placed.  

    :argument str basedir: the desired path to tmp directory's parent directory.
                           if not provided, the directory will be placed in the 
                           current working directory.
    :argument str dirname: the desired name for the directory
    :return str: the path to the temporary directory
    """
    if not dirname:
        dirname = tmpname
    if not basedir:
        basedir = os.getcwd()
    return os.path.join(basedir, dirname)

def rmdir(dirpath):
    """
    remove the given path and all its contents
    """
    shutil.rmtree(dirpath)

def rmtmpdir(basedir=None, dirname=None):
    """
    remove the default 

    :argument str basedir: the path to tmp directory's parent directory.
                           if not provided, the current working directory will 
                           be assumed.
    :argument str dirname: the name for the directory
    :return str: the path to the removed temporary directory
    """
    tdir = tmpdir(basedir, dirname)
    if os.path.exists(tdir):
        rmdir(tdir)

class Tempfiles(object):

    def __init__(self, tempdir=None):
        if not tempdir:
            tempdir = ensure_tmpdir()
        assert os.path.exists(tempdir)
        self._parent = tempdir
        self._files = set()

    @property
    def parent(self):
        return self._parent

    def mkdir(self, dirname):
        d = os.path.join(self.parent, dirname)
        if not os.path.isdir(d):
            os.mkdir(d)
        self.track(dirname)
        return d

    def track(self, filename):
        self._files.add(filename)

    def clean(self):
        for i in xrange(len(self._files)):
            filen = self._files.pop()
            path = os.path.join(self._parent, filen)
            if os.path.exists(path):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                finally:
                    if os.path.exists(path):
                        self._files.add(filen)


