## myles targets

# PLEASE FOR TO BE CHECKING FOR AND ADDING/SETTING IDENTITY FILE STUFF
# TO rsync/ssh CALLS BELOW (20170905/thisisaaronland)

### STAGING_TARGET=

myles-block-deploy:
	$(eval BLOCK_FILE := $(shell echo $(STAGING_TARGET) | shasum -a 256 | awk '{ print $$1 }'))
	if test ! -f /tmp/$(BLOCK_FILE); then echo `date` > /tmp/$(BLOCK_FILE); fi
	echo "wrote block file /tmp/$(BLOCK_FILE)"

### STAGING_TARGET=

myles-unblock-deploy:
	$(eval BLOCK_FILE := $(shell echo $(STAGING_TARGET) | shasum -a 256 | awk '{ print $$1 }'))
	if test -f /tmp/$(BLOCK_FILE); then rm /tmp/$(BLOCK_FILE); fi

### STAGING_TARGET=

myles-ensure-unblocked:
	$(eval BLOCK_FILE := $(shell echo $(STAGING_TARGET) | shasum -a 256 | awk '{ print $$1 }'))
	if test -f /tmp/$(BLOCK_FILE); then echo "deploy is blocked"; exit 1; fi

### STAGING_SOURCE= STAGING_TARGET=

myles-stage-site:
	@make myles-ensure-unblocked
	sudo rm -rf $(STAGING_TARGET)
	$(GIT) clone $(STAGING_SOURCE) $(STAGING_TARGET)
	rm -rf $(STAGING_TARGET)/.git
	rm -rf $(STAGING_TARGET)/.apache
	rm -rf $(STAGING_TARGET)/.ubuntu
	rm -rf $(STAGING_TARGET)/.schema
	rm -rf $(STAGING_TARGET)/.extras
	sudo chown -R www-data $(STAGING_TARGET)/www/templates_c
	perl -p -i -e 's/php_flag display_errors\s+on/php_flag display_errors off/' $(STAGING_TARGET)/www/.htaccess

### STAGING_TARGET= DEPLOY_TARGET= DEPLOY_HOSTS=

myles-deploy-site:
	$(foreach h, $(shell cat $(DEPLOY_HOSTS) | grep -v -e '^#' | awk '{ print $$1 }'), make myles-deploy-site-for-host STAGING_TARGET=$(STAGING_TARGET) DEPLOY_HOST=$(h) DEPLOY_TARGET=$(DEPLOY_TARGET);)

### STAGING_TARGET= DEPLOY_TARGET= DEPLOY_HOST=

myles-deploy-site-for-host:
	@make myles-ensure-unblocked STAGING_TARGET=$(STAGING_TARGET)
	@make myles-block-deploy STAGING_TARGET=$(STAGING_TARGET)
	@make myles-disable-host DEPLOY_HOST=$(DEPLOY_HOST)
	$(eval DEPLOY_ADDR := $(shell echo $(DEPLOY_HOST) | awk -F ':' '{ print $$1 }'))
	$(RSYNC) -e ssh -a -z --delete --safe-links --omit-dir-times --cvs-exclude --exclude=templates_c --exclude=config_dev.php --exclude=config_local_${WHOAMI}.php $(STAGING_TARGET)/ $(DEPLOY_ADDR):$(DEPLOY_TARGET)
	@make myles-enable-host
	@make myles-unblock-deploy STAGING_TARGET=$(STAGING_TARGET)

### STAGING_TARGET= DEPLOY_TARGET= DEPLOY_HOSTS=

myles-deploy-config:
	$(foreach h, $(shell cat $(DEPLOY_HOSTS) | grep -v -e '^#' | awk '{ print $$1 }'), @make myles-deploy-config-for-host DEPLOY_HOST=$(h) STAGING_TARGET=$(STAGING_TARGET) DEPLOY_TARGET=$(DEPLOY_TARGET);)

### STAGING_TARGET= DEPLOY_TARGET= DEPLOY_HOST=

myles-deploy-config-for-host:
	@make myles-ensure-unblocked STAGING_TARGET=$(STAGING_TARGET)
	@make myles-block-deploy STAGING_TARGET=$(STAGING_TARGET)
	$(eval DEPLOY_ADDR := $(shell echo $(DEPLOY_HOST) | awk -F ':' '{ print $$1 }'))
	$(RSYNC) -e ssh -v -a -z $(STAGING_TARGET)/www/include/config.php $(STAGING_TARGET)/www/include/config_local.php $(STAGING_TARGET)/www/include/secrets.php $(DEPLOY_ADDR):$(DEPLOY_TARGET)
	@make myles-unblock-deploy STAGING_TARGET=$(STAGING_TARGET)

### DEPLOY_HOSTS= DEPLOY_TARGET=

myles-disable-site:
	$(foreach h, $(shell cat $(DEPLOY_HOSTS) | grep -v -e '^#' | awk '{ print $$1 }'), @make myles-disable-host DEPLOY_TARGET=$(DEPLOY_TARGET) DEPLOY_HOST=$(h);)

### DEPLOY_HOSTS= DEPLOY_TARGET=

myles-enable-site:
	$(foreach h, $(shell cat $(DEPLOY_HOSTS) | grep -v -e '^#' | awk '{ print $$1 }'), @make myles-enable-host DEPLOY_TARGET=$(DEPLOY_TARGET) DEPLOY_HOST=$(h);)

### DEPLOY_HOST= DEPLOY_TARGET=

myles-disable-host:
	$(eval DEPLOY_ADDR := $(shell echo $(DEPLOY_HOST) | awk -F ':' '{ print $$1 }'))
	$(SSH) -q -t $(shell echo $(DEPLOY_ADDR) | awk -F ':' '{ print $$1 }') $(DEPLOY_TARGET)/bin/disable_site.sh
	@make myles-ensure-disabled DEPLOY_HOST=$(DEPLOY_HOST)

### DEPLOY_HOST= DEPLOY_TARGET=

myles-enable-host:
	$(eval DEPLOY_ADDR := $(shell echo $(DEPLOY_HOST) | awk -F ':' '{ print $$1 }'))
	$(SSH) -q -t $(DEPLOY_ADDR) $(DEPLOY_TARGET)/bin/enable_site.sh
	@make myles-ensure-enabled DEPLOY_HOST=$(DEPLOY_HOST)

### DEPLOY_HOST=

myles-ensure-enabled:
	$(eval STATUS_CODE := $(shell $(CURL) -s -I $(DEPLOY_HOST) | grep HTTP | awk '{ print $$2 }'))
	if test "$(STATUS_CODE)" != "200"; then "$(DEPLOY_HOST) is not up w/ status code $(STATUS_CODE)"; sleep 2; make myles-ensure-enabled DEPLOY_HOST=$(DEPLOY_HOST); fi

### DEPLOY_HOST=

myles-ensure-disabled:
	$(eval STATUS_CODE := $(shell $(CURL) -s -I $(DEPLOY_HOST) | grep HTTP | awk '{ print $$2 }'))
	if test "$(STATUS_CODE)" = "200"; then "$(DEPLOY_HOST) is reporting that it is up w/ status code $(STATUS_CODE)"; sleep 2; make myles-ensure-disabled DEPLOY_HOST=$(DEPLOY_HOST); fi
