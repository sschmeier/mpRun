#!/usr/bin/env bash

git checkout master
git pull origin master;

chmod a+x ./mprun.py

function doIt() {
	rsync --exclude ".git/" --exclude ".DS_Store" --exclude "bootstrap.sh"  \
		--exclude "README.md" --exclude "LICENSE" -avh --no-perms mprun.py ~/bin;
}

if [ "$1" == "--force" -o "$1" == "-f" ]; then
	doIt;
else
	read -p "This may overwrite existing files in your bin directory. Are you sure? (y/n) " -n 1;
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		doIt;
	fi;
fi;
unset doIt;

git checkout develop
