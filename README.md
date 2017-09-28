# flamework-deploy

Tools for deploying Flamework applications.

## Important

If you are looking for the version of `flamework-deploy` that used a variety of Python libraries and tools for deploying applications, it can be found over here: https://github.com/whosonfirst/flamework-deploy/releases/tag/1.0.0

## Myles

`myles` is the prefix for a series of `make` targets (defined in [myles/Makefile](myles/Makefile)) for deploying Flamework applications. You can invoke them as-is or wrap them in your custom targets, specific to your application. For example:

```
example-deploy-site:
        if test "$(DEPLOY_HOSTS_ROOT)" = ""; then echo "you forgot to specify DEPLOY_HOSTS_ROOT"; exit 1; fi
        $(eval DEPLOY_HOSTS := "${DEPLOY_HOSTS_ROOT}/hosts_${ENV}.txt")
        if test ! -f $(DEPLOY_HOSTS); then echo "hosts file ($(DEPLOY_HOSTS)) does not exist"; exit 1; fi
        @make myles-deploy-site STAGING_TARGET=$(STAGING_TARGET) DEPLOY_TARGET=$(DEPLOY_TARGET) DEPLOY_HOSTS=$(DEPLOY_HOSTS)
```

### Targets

`myles` defines the following targets:

#### myles-block-deploy

* STAGING_TARGET= _please write me_

#### myles-unblock-deploy

* STAGING_TARGET= _please write me_

#### myles-ensure-unblocked

* STAGING_TARGET= _please write me_

#### myles-stage-site

* STAGING_SOURCE= _please write me_
* STAGING_TARGET= _please write me_

#### myles-deploy-site

* STAGING_TARGET= _please write me_
* DEPLOY_TARGET= _please write me_
* DEPLOY_HOSTS= _please write me_

#### myles-deploy-site-for-host

* STAGING_TARGET= _please write me_
* DEPLOY_TARGET= _please write me_
* DEPLOY_HOST= _please write me_

#### myles-deploy-config

* STAGING_TARGET= _please write me_
* DEPLOY_TARGET= _please write me_
* DEPLOY_HOSTS= _please write me_

#### myles-deploy-config-for-host

* STAGING_TARGET= _please write me_
* DEPLOY_TARGET= _please write me_
* DEPLOY_HOST= _please write me_

#### myles-disable-site

* DEPLOY_HOSTS= _please write me_
* DEPLOY_TARGET= _please write me_

#### myles-enable-site

* DEPLOY_HOSTS= _please write me_
* DEPLOY_TARGET= _please write me_

#### myles-disable-host

* DEPLOY_HOST= _please write me_
* DEPLOY_TARGET= _please write me_

#### myles-enable-host

* DEPLOY_HOST= _please write me_
* DEPLOY_TARGET= _please write me_

#### myles-ensure-enabled

* DEPLOY_HOST= _please write me_

#### myles-ensure-disabled

* DEPLOY_HOST= _please write me_

### Hosts

`myles` read hosts for deploy code to from plain-text files that look like this:

```
127.0.0.1		# example-1
127.0.0.2:8080		# example-2
# 127.0.0.2:8081	# example-3
```

Entries starting with a `#` are ignored.

### Config files

_please write me_

