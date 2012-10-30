#!/usr/bin/env python2


import cmd
import shlex
import subprocess
import os
import shutil


class TklPatcher(cmd.Cmd):
    """
    A quick and dirty shell that automatically generates a tkl-patch as
    you execute commands in it
    """
    intro = """A quick and dirty shell that automatically generates a tkl-patch
as you execute commands in it.  Use Ctrl + D to exit
"""

    _cwd = os.getcwd()
    _templateFile = os.path.dirname(__file__) + '/conf-template'

    def _createDirectory(self, directory):
        print "Creating %s" % directory
        if not os.path.exists(directory):
            os.mkdir(directory)
            print "Done"
        else:
            print "Exists"

    def _createSkeletonConfFile(self, filePath):
        content = ''
        if os.path.exists(self._templateFile):
            f = open(self._templateFile, 'r')
            for line in f:
                content += line
            f.close()
            print "Creating %s" % filePath
            if not os.path.exists(filePath):
                f = open(filePath, 'w')
                content = (content % (self._patchName)) + '\n'
                f.write(content)
                f.close()
                os.chmod(self.confFile, 0775)
                print "Done"
            else:
                print "Exists"
        else:
            print "conf-template not found at %s" % (self._templateFile)

    def _writeCommandToConfFile(self, command):
        f = open(self.confFile, 'a')
        f.write(command + '\n')
        f.close()

    def _createSkeletonPatch(self):
        self._createDirectory(self.patchDirectory)
        self._createDirectory(self.patchDebsDirectory)
        self._createDirectory(self.patchOverlayDirectory)
        self._createSkeletonConfFile(self.confFile)

    def do_use(self, args):
        """
        use [package-name]
        This creates a basic TKL package folder with the given name in the
        current directory.

        If a package with the given name already exists in
        the current directory, it is used and all the changes will be appended
        to the existing package.

        The conf-template file is used as a skeleten for conf
        """
        args = shlex.split(args)
        if len(args) > 0:
            self._patchName = args[0]
            self.patchDirectory = self._cwd + '/' + self._patchName
            self.patchDebsDirectory = self.patchDirectory + '/debs'
            self.patchOverlayDirectory = self.patchDirectory + '/overlay'
            self.confFile = self.patchDirectory + '/conf'
            self._createSkeletonPatch()
        else:
            print "Patch name not specified"

    def do_install(self, args):
        """
        install [package-name]
        The shell runs "apt-get install <package-name>" command for the user
        But enters "install <package-name>" into the conf file where install is
        the following bash function:
            install()
            {
                apt-get update
                DEBIAN_FRONTEND=noninteractive apt-get -y \\
                -o DPkg::Options::=--force-confdef \\
                -o DPkg::Options::=--force-confold \\
                install $@
            }

        If this is not in the conf-template file, the generated conf file will
        fail
        """
        command = 'apt-get update && apt-get install' + args
        print "Running command: %s" % (command)
        command = shlex.split(command)
        returnCode = subprocess.call(command)
        if returnCode == 0:
            for package in args.split():
                command = "install %s" % package
                print "Adding command (%s) to conf file" % command
                self._writeCommandToConfFile(command)
                print "Done"
        else:
            print "Error skipping command"

    def do_test(self, args):
        """
        test [command]
        Used to execute linux commands. This commands will not be added to the
        conf file
        """
        command = shlex.split(args)
        print "Testing command without writing to conf: %s" % (args)
        subprocess.call(command)

    def do_shell(self, args):
        """
        shell [command] or ![command]
        Used to execute linux commands. This commands will be added to the
        conf file
        """
        command = shlex.split(args)
        print "Running command: %s" % (args)
        returnCode = subprocess.call(command)
        if returnCode == 0:
            print "Adding command to conf file"
            self._writeCommandToConfFile(args)
            print "Done"
        else:
            print "Error skipping command"

    def do_edit(self, args):
        """
        edit [file-name]
        The given filename will be opened in editor. The changed file is then
        copied to the overlays folder with its folder tree
        """
        filePath = os.path.abspath(args)
        command = ['nano']
        command += shlex.split(filePath)
        subprocess.call(command)
        print "Copying changed file (%s) to overlay" % filePath
        fileDirectoryPath = os.path.dirname(filePath)
        os.makedirs(self.patchOverlayDirectory + fileDirectoryPath)
        shutil.copy(filePath, self.patchOverlayDirectory + fileDirectoryPath)
        print "Done"

    def do_EOF(self, args):
        print "Bye"
        return True

if __name__ == '__main__':
    TklPatcher().cmdloop()
