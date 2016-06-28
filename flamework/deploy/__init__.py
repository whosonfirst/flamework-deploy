import os
import sys
import logging
import time

import subprocess

class base:

    def __init__(self, **kwargs):

        self.root = None
        self.app = None
        self.identity = None
        
        self.setup(**kwargs)

    def setup(self, **kwargs):

        raise Exception, "Invalid setup"

    def hosts(self):

        hosts = os.path.join(self.root, "hosts")
        hosts_txt = os.path.join(hosts, "hosts.txt")

        fh = open(hosts_txt, "r")

        for ln in fh.readlines():
            
            ln = ln.strip()

            if ln.startswith("#"):
                continue

            yield ln

    def disable_host(self, host):

        logging.info("disable host %s" % host)
        
        bin = os.path.join(self.app, "bin")
        disable = os.path.join(bin, "disable-site.php")
        
        cmd = [
            "php",
            "-q",
            disable
        ]

        return self._ssh(host, cmd)

    def enable_host(self, host):

        logging.info("enable host %s" % host)
                
        bin = os.path.join(self.app, "bin")
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

        return "https://%s" % host
    
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
    
