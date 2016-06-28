RSYNC = $(shell which rsync)

MASTER = "FIX ME"
STAGING = "FIX ME"

staging:
	@echo "staging"
	cd $(MASTER)
	git pull origin master
	cd -
	$(RSYNC) $(MASTER) $(STAGING)
	cd $(STAGING)
	rm -rf .git

deploy: ok-for-deploy
	block-deploy
	@echo "deploy"	
	# bin/flamework-deploy-site --config flamework.cfg --hosts hosts/hosts.txt $(STAGING)
	unblock-deploy

ok-for-deploy:
	if test -f deploy.lock; then echo "NOT OK FOR DEPLOY" && exit 1; fi

block-deploy:
	touch deploy.lock

unblock-deploy:
	if test -f deploy.lock; then rm deploy.lock; fi
