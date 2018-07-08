# -*- coding: utf-8 -*-
import subprocess

class ProcessError(Exception):
    """This exception is raised when an isis process returns a non-zero exit
    status.
    """
    def __init__(self, returncode, cmd, stdout, stderr):
        self.returncode = returncode
        self.cmd = cmd
        self.stdout = stdout
        self.stderr = stderr

        msg = "Command '%s' returned non-zero exit status %d"
        super(ProcessError, self).__init__(msg % (self.cmd[0], self.returncode))

    def __reduce__(self):
        return (self.__class__, (
            self.returncode,
            self.cmd,
            self.stdout,
            self.stderr,
        ))

class ISISError(Exception):
    """This exception is raised when an isis process returns a non-zero exit
    status.
    """
    def __init__(self, returncode, cmd, img):
        self.returncode = returncode
        self.cmd = cmd
        self.img = img

        msg = "Fail on %s"
        super(ISISError, self).__init__(msg % self.img)

    def __reduce__(self):
        return (self.__class__, (
            self.returncode,
            self.cmd,
            self.img,
        ))

def call(cmd):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        output, err = process.communicate()
    except:
        process.kill()
        process.wait()
        raise

    retcode = process.poll()
    if retcode:
        raise ProcessError(retcode, cmd, stdout=output, stderr=err)
