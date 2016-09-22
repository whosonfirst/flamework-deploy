# https://pythonhosted.org/setuptools/setuptools.html#namespace-packages
__import__('pkg_resources').declare_namespace(__name__)

import os
import sys
import logging
import time
import shutil
import subprocess

class base:

    def __init__(self, name, cfg, **kwargs):

        self.name = name
        self.source = cfg.get(name, 'source')
        self.staging = cfg.get(name, 'staging') 
        self.remote = cfg.get(name, 'remote')        
        self.hosts = cfg.get(name, 'hosts')
        self.identity = cfg.get(name, 'identity')
        self.config = cfg.get(name, 'config')                

        self.staging = os.path.abspath(self.staging)
        self.config = os.path.abspath(self.config)

        self.hosts = os.path.abspath(self.hosts)
        self.identity = os.path.abspath(self.identity)

        for path in (self.staging, self.config):

            if not os.path.exists(path):
                raise Exception, "%s does not exist" % path

            if not os.path.isdir(path):
                raise Exception, "%s is not a directory" % path

        for path in (self.hosts, self.identity):

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

        hosts_txt = os.path.abspath(self.hosts)

        fh = open(hosts_txt, "r")

        for ln in fh.readlines():
            
            ln = ln.strip()

            if ln.startswith("#"):
                continue

            yield ln

    def stage_site(self):

        dotgit = os.path.join(self.staging, ".git")

        www = os.path.join(self.staging, "www")
        include = os.path.join(www, "include")

        config_local = os.path.join(include, "config_local/.php")
        htaccess = os.path.join(www, ".htaccess")

        logging.info("purge contents of %s" % self.staging)

        for root, dirs, files in os.walk(self.staging):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))

        logging.info("clone %s in to %s" % (self.source, self.staging))

        logging.info("remove %s" % dotgit)
        # shutil.rmtree(dotgit)

        for config in ('config_local.php', 'config_staging.php', 'secrets.php'):

            local_path = os.path.join(self.config, config)
            staging_path = os.path.join(include, config)

            if os.path.exists(local_path):

                logging.info("copy %s to %s" % (local_path, staging_path))
                # shutil.copyfile(local_path, staging_path)
        
        logging.info("ensure errors are disabled in %s" % htaccess)

        logging.info("set $GLOBALS['cfg']['environment'] in %s" % config_local)


    def disable_host(self, host):

        logging.info("disable host %s" % host)
        
        bin = os.path.join(self.remote, "bin")
        disable = os.path.join(bin, "disable-site.php")
        
        cmd = [
            "php",
            "-q",
            disable
        ]

        return self._ssh(host, cmd)

    def enable_host(self, host):

        logging.info("enable host %s" % host)
                
        bin = os.path.join(self.remote, "bin")
        enable = os.path.join(bin, "enable-site.php")
        
        cmd = [
            "php",
            "-q",
            enable
        ]

        return self._ssh(host, cmd)

    def is_host_enabled(self, host):

        url = self.url_for_host(host)

        rsp = requests.get(url)

        if rsp.status_code == 200:
            return True

        return False

    def is_host_disabled(self, host):

        url = self.url_for_host(host)
        rsp = requests.get(url)

        # because this: https://github.com/whosonfirst/flamework/blob/master/www/include/init.php#L435-L460
        
        if rsp.status_code == 502:
            return True

        return False
        
    def deploy_site(self):

        for host in self.hosts():
            self.deploy_site_for_host(host)

    def deploy_config(self):

        for host in self.hosts():
            self.deploy_config_for_host(host)
            
    def deploy_site_for_host(self, host):

        logging.info("deploy site for %s" % host)
        
        self.disable_host(host)

        while not self.is_host_disabled(host):

            logging.debug("%s is not disabled, waiting" % host)
            time.sleep(1)

        # DO STUFF

        self.enable_host(host)

        while not self.is_host_enabled(host):

            logging.debug("%s is not enabled, waiting" % host)            
            time.sleep(1)

    def deploy_config_for_host(self, host):

        logging.info("deploy config for %s" % host)
        
    def url_for_host(self, host):

        return "%s://%s" % (self. scheme, host)
    
    def _ssh(self, host, cmd):

        ssh_cmd = [
            "ssh",
            "-i",
            self.identity,
        ]

        ssh_cmd.extend(cmd)

        logging.debug(" ".join(ssh_cmd))
        
        out = subprocess.check_output(cmd)

    def _scp(self, host, cmd):

        scp_cmd = [
            "scp",
            "-i",
            self.identity
        ]

        scp_cmd.extend(cmd)

        logging.debug(" ".join(scp_cmd))
                
        out = subprocess.check_output(cmd)

    def _rsync(self, host):
        pass
    
