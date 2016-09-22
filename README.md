# flamework-deploy

Too soon. Everything here will change.

## Things this tool needs

* Path to a Flamework-derived project, remote
* Path to a Flamework-derived project Git source
* Path to a staging folder
* Path to an identify file (for scp and rsync)
* Path to a list of hosts
* Path to a config folder containing config_local, secrets and optionally config_staging

## myles

### stage-site

```
./myles -n api -c ../../api/api.cfg stage-site
INFO:root:purge contents of /usr/local/mapzen/api/staging
INFO:root:clone https://github.com/whosonfirst/whosonfirst-www-api.git in to /usr/local/mapzen/api/staging
INFO:root:remove /usr/local/mapzen/api/staging/.git
INFO:root:copy /usr/local/mapzen/api/config/config_local.php to /usr/local/mapzen/api/staging/www/include/config_local.php
INFO:root:copy /usr/local/mapzen/api/config/config_staging.php to /usr/local/mapzen/api/staging/www/include/config_staging.php
INFO:root:copy /usr/local/mapzen/api/config/secrets.php to /usr/local/mapzen/api/staging/www/include/secrets.php
INFO:root:ensure errors are disabled in /usr/local/mapzen/api/staging/www/.htaccess
INFO:root:set $GLOBALS['cfg']['environment'] in /usr/local/mapzen/api/staging/www/include/config_local/.php
```

### deploy-config

### deploy-site

### enable-host

### disable-host

