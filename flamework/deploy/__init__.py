import os
import sys
import logging
import time

import subprocess

class base:

    def __init__(self, cfg, **kwargs):

        self.local = cfg.get('flamework-deploy', 'local')
        self.remote = cfg.get('flamework-deploy', 'remote')        
        self.hosts = cfg.get('flamework-deploy', 'hosts')
        self.identity = cfg.get('flamework-deploy', 'identity')
        self.config = cfg.get('flamework-deploy', 'config')                
        self.secrets = cfg.get('flamework-deploy', 'secrets')

        # put this in the config? probably...
        self.scheme = kwargs.get('scheme', 'https')
        
        self.setup()

    def setup(self):

        # please validate everything here
        
    def hosts(self):

        hosts_txt = os.path.abspath(self.hosts)

        fh = open(hosts_txt, "r")

        for ln in fh.readlines():
            
            ln = ln.strip()

            if ln.startswith("#"):
                continue

            yield ln

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
    
