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

        self.dryrun = kwargs.get('dryrun', False)

        self.ssh = kwargs.get('ssh', 'ssh')
        self.scp = kwargs.get('ssh', 'scp')
        self.rsync = kwargs.get('rsync', 'rsync')
        self.git = kwargs.get('git', 'git')
        self.perl = kwargs.get('perl', 'perl')

        #

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
        apache = os.path.join(self.staging, "apache")
        ubuntu = os.path.join(self.staging, "ubuntu")
        schema = os.path.join(self.staging, "schema")

        www = os.path.join(self.staging, "www")
        include = os.path.join(www, "include")

        config_local = os.path.join(include, "config_local.php")
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

        for remove in (dotgit, apache, ubuntu, schema):

            logging.info("remove %s" % remove)

            if not self.dryrun:
                shutil.rmtree(remove)

        # copy

        for config in ('config_local.php', 'config_staging.php', 'secrets.php'):

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
            subprocess.check_output(cmd, shell=True)

        # prep (config local)

        logging.info("set $GLOBALS['cfg']['environment'] in %s" % config_local)

        replace = "s/$GLOBALS['cfg']['environment']\s*=\s*['\\\"][^'\\\"]+['\\\"];/$GLOBALS['cfg']['environment'] = 'staging';/"

        cmd = [
            self.perl,
            "-p", "-i", "-e",
            "\"%s\"" % replace,
            config_local
        ]

        logging.info(" ".join(cmd))

        if not self.dryrun:
            subprocess.check_output(cmd, shell=True)

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

        logging.info(" ".join(ssh_cmd))
        
        if not self.dryrun:
            out = subprocess.check_output(cmd)

    def _scp(self, host, cmd):

        scp_cmd = [
            "scp",
            "-i",
            self.identity
        ]

        scp_cmd.extend(cmd)

        logging.info(" ".join(scp_cmd))
                
        if not self.dryrun:
            out = subprocess.check_output(cmd)

    def _rsync(self, host):
        pass
    
