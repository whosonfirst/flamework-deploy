# https://pythonhosted.org/setuptools/setuptools.html#namespace-packages
__import__('pkg_resources').declare_namespace(__name__)

import os
import sys
import logging
import time
import shutil
import subprocess
import tempfile

import requests

class base:

    def __init__(self, name, cfg, **kwargs):

        self.name = name
        self.source = cfg.get(name, 'source')
        self.staging = cfg.get(name, 'staging') 
        self.remote = cfg.get(name, 'remote')        
        self.hostsfile = cfg.get(name, 'hosts')
        self.identity = cfg.get(name, 'identity')
        self.config = cfg.get(name, 'config')                

        # sudo make me required in the config...

        lockname = "%s.lock" % self.name
        self.lock = os.path.join(tempfile.gettempdir(), lockname)

        self.dryrun = kwargs.get('dryrun', False)
        self.scheme = kwargs.get('scheme', 'http')	# DO NOT MAKE ME THE DEFAULT...

        self.ssh = kwargs.get('ssh', 'ssh')
        self.scp = kwargs.get('ssh', 'scp')
        self.rsync = kwargs.get('rsync', 'rsync')
        self.git = kwargs.get('git', 'git')
        self.perl = kwargs.get('perl', 'perl')

        #

        self.staging = os.path.abspath(self.staging)
        self.config = os.path.abspath(self.config)

        self.hostsfile = os.path.abspath(self.hostsfile)
        self.identity = os.path.abspath(self.identity)

        for path in (self.staging, self.config):

            if not os.path.exists(path):
                raise Exception, "%s does not exist" % path

            if not os.path.isdir(path):
                raise Exception, "%s is not a directory" % path

        for path in (self.hostsfile, self.identity):

            if not os.path.exists(path):
                raise Exception, "%s does not exist" % path
        
        for cfg in ('config_local.php', 'secrets.php'):

            cfg_path = os.path.join(self.config, cfg)

            if not os.path.exists(cfg_path):
                raise Exception, "%s is missing" % cfg_path

        for target in (self.remote, self.source):

            if target == "":
                raise Exception, "%s is empty" % "FIXME"

    def hosts(self):

        hosts_txt = os.path.abspath(self.hostsfile)
        
        fh = open(hosts_txt, "r")

        for ln in fh.readlines():
            
            ln = ln.strip()

            if ln.startswith("#"):
                continue

            parts = ln.split("#")
            
            yield parts[0].strip()

    def is_valid_host(self, host):

        for test in self.hosts():

            if test == host:
                return True

        return False

    def stage_site(self):

        if not self.lock_deploy():
            logging.error("failed to lock deploy")
            return False

        dotgit = os.path.join(self.staging, ".git")
        apache = os.path.join(self.staging, "apache")
        ubuntu = os.path.join(self.staging, "ubuntu")
        schema = os.path.join(self.staging, "schema")
        extras = os.path.join(self.staging, "extras")
        makefile = os.path.join(self.staging, "Makefile")

        www = os.path.join(self.staging, "www")
        include = os.path.join(www, "include")

        config_global = os.path.join(include, "config.php")
        config_local = os.path.join(self.config, "config_local.php")
        config_staging = os.path.join(include, "config_staging.php")

        htaccess = os.path.join(www, ".htaccess")

        # clean up

        logging.info("purge contents of %s" % self.staging)

        if not self.dryrun:

            for root, dirs, files in os.walk(self.staging):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))

        # clone 

        logging.info("clone %s in to %s" % (self.source, self.staging))

        cmd = [
            self.git,
            "clone",
            self.source,
            self.staging
        ]

        logging.info(" ".join(cmd))

        if not self.dryrun:
            out = subprocess.check_output(cmd)
            logging.debug(out)

        # prune

        for remove in (dotgit, apache, ubuntu, schema, extras, makefile):

            logging.info("remove %s" % remove)

            if not self.dryrun:

                if os.path.isdir(remove):
                    shutil.rmtree(remove)
                else:
                    os.unlink(remove)

        # append
        
        logging.info("append custom config to global config")

        if not self.dryrun:

            global_fh = open(config_global, "a")
            local_fh = open(config_local, "r")

            global_fh.write("\n")

            for ln in local_fh.readlines():
                global_fh.write(ln)

            global_fh.close()
            local_fh.close()

        # copy

        for config in ('config_staging.php', 'secrets.php'):

            local_path = os.path.join(self.config, config)
            staging_path = os.path.join(include, config)

            if os.path.exists(local_path):

                logging.info("copy %s to %s" % (local_path, staging_path))

                if not self.dryrun:
                    shutil.copyfile(local_path, staging_path)
        
        # prep (htaccess)

        logging.info("ensure errors are disabled in %s" % htaccess)

        replace = "s/php_flag display_errors\s+on/php_flag display_errors off/"

        cmd = [
            self.perl,
            "-p", "-i", "-e",
            "\"%s\"" % replace,
            htaccess
        ]

        logging.info(" ".join(cmd))

        if not self.dryrun:

            # not happy about this but it appears to be the only way?
            # (20160922/thisisaaronland)
            # subprocess.call(cmd)

            os.system(" ".join(cmd))

        # prep (config local)

        logging.info("set $GLOBALS['cfg']['environment'] in %s" % config)

        replace = "s/\\['cfg'\\]\\['environment'\\]\s*=\s*'[^']+'/['cfg']['environment'] = 'prod'/"

        cmd = [
            self.perl,
            "-p", "-i", "-e",
            "\"%s\"" % replace,
            config_global
        ]

        logging.info(" ".join(cmd))

        if not self.dryrun:

            # not happy about this but it appears to be the only way?
            # (20160922/thisisaaronland)
            # subprocess.call(cmd)

            os.system(" ".join(cmd))

        return self.unlock_deploy()

    def disable_host(self, host):

        logging.info("disable host %s" % host)
        
        bin = os.path.join(self.remote, "bin")
        disable = os.path.join(bin, "disable_site.sh")		# https://github.com/whosonfirst/flamework-tools/blob/master/flamework-bin/disable_site.sh
        
        cmd = [
            disable
        ]

        return self._ssh(host, cmd)

    def enable_host(self, host):

        logging.info("enable host %s" % host)
                
        bin = os.path.join(self.remote, "bin")
        enable = os.path.join(bin, "enable_site.sh")		# https://github.com/whosonfirst/flamework-tools/blob/master/flamework-bin/enable_site.sh
        
        cmd = [
            enable
        ]

        return self._ssh(host, cmd)

    def is_host_enabled(self, host):

        url = self.url_for_host(host)

        logging.info("check if %s is enabled (%s)" % (host, url))

        if self.dryrun:
            return True

        rsp = requests.get(url)

        if rsp.status_code == 200:
            return True

        return False

    def is_host_disabled(self, host):

        url = self.url_for_host(host)
        rsp = requests.get(url)

        logging.info("check if %s is disabled (%s)" % (host, url))

        if self.dryrun:
            return True

        if rsp.status_code == 420:
            return True

        return False
        
    def deploy_site(self):

        if not self.lock_deploy():
            logging.error("failed to lock deploy")
            return False

        for host in self.hosts():

            if not self.deploy_site_for_host(host):
                return False

        # see the way the deploy lock isn't being removed if there's
        # an error above? that's on purpose (20160923/thisisaaronland)

        return self.unlock_deploy()

    def deploy_config(self):

        if not self.lock_deploy():
            logging.error("failed to lock deploy")
            return False

        for host in self.hosts():

            if not self.deploy_config_for_host(host):
                return False

        # see the way the deploy lock isn't being removed if there's
        # an error above? that's on purpose (20160923/thisisaaronland)
            
        return self.unlock_deploy()

    def deploy_site_for_host(self, host):

        logging.info("deploy site for %s" % host)
        
        self.disable_host(host)

        while not self.is_host_disabled(host):

            logging.debug("%s is not disabled, waiting" % host)
            time.sleep(1)

        if not self._rsync(host, self.staging, self.remote):
            return False

        self.enable_host(host)

        while not self.is_host_enabled(host):

            logging.debug("%s is not enabled, waiting" % host)            
            time.sleep(1)

        return True

    def deploy_config_for_host(self, host):

        logging.info("deploy config for %s" % host)

        configs = []
        
        local_www = os.path.join(self.staging, "www")
        local_include = os.path.join(local_www, "include")

        config = os.path.join(local_include, "config.php")
        config_local = os.path.join(local_include, "config_local.php")
        secrets = os.path.join(local_include, "secrets.php")

        remote_www = os.path.join(self.remote, "www")
        remote_include = os.path.join(remote_www, "include")

        config_files = (config, secrets)

        if os.path.exists(config_local):
            config_files.append(config_local)

        for cfg in config_files:

            if not self._scp(host, cfg, remote_include):
                logging.error("failed to update %s on %s" % (src, host))
                return False

        return True

    def url_for_host(self, host):

        return "%s://%s" % (self. scheme, host)

    def lock_deploy(self):

        lock = self.deploy_lock()

        if os.path.exists(lock):
            logging.error("lockfile (%s) already exists" % lock)
            return False

        t = str(time.time())

        fh = open(lock, "w")
        fh.write(t)
        fh.close()

        return True

    def unlock_deploy(self):

        lock = self.deploy_lock()

        if os.path.exists(lock):
            os.unlink(lock)
        
        return True

    def is_deploy_locked(self):

        lock = self.deploy_lock()
        return os.path.exists(lock)

    def deploy_lock(self):
        return self.lock

    def _ssh(self, host, cmd):

        ssh_cmd = [
            "ssh",
            "-q",
            "-t",	# https://stackoverflow.com/questions/12480284/ssh-error-when-executing-a-remote-command-stdin-is-not-a-tty
            "-i", self.identity,
            host
        ]

        ssh_cmd.extend(cmd)

        logging.info(" ".join(ssh_cmd))

        if self.dryrun:
            return True

        return self._popen(ssh_cmd)

    def _scp(self, host, src, dest):

        dest = "%s:%s" % (host, dest)

        scp_cmd = [
            "scp",
            "-q",
            "-i", self.identity,
            src,
            dest,
        ]

        logging.info(" ".join(scp_cmd))
                
        if self.dryrun:
            return True

        return self._popen(scp_cmd)

    def _rsync(self, host, src, dest):

        src = src.rstrip("/") + "/"
        dest = "%s:%s" % (host, dest)

        rsync_cmd = [
            self.rsync,
            "-e",
            "\"ssh -o IdentityFile=%s\"" % self.identity,
            # "ssh",
            "-a", "-z",
            # "-v",
            "--delete",
            "--safe-links",
            "--cvs-exclude",
            "--exclude=templates_c",
            "--exclude=config_staging.php",
            src,
            dest,
        ]

        logging.info(" ".join(rsync_cmd))
                
        if self.dryrun:
            return True

        return self._popen(rsync_cmd)

    def _popen(self, cmd):

        logging.debug("popen with %s" % " ".join(cmd))

        prog = subprocess.Popen(cmd, stderr=subprocess.PIPE, shell=False)
        rsp = prog.communicate()

        # logging.debug("popen response: %s" % rsp)

        err = rsp[1]

        # the 'stdin: is not a tty' thing... I don't really understand
        # why this is happening... (20160923/thisisaaronland)

        if err != '' and err != "stdin: is not a tty\n":
            logging.error("popen command failed: %s" % err)
            return False

        return True
