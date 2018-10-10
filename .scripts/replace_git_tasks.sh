#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Please insert the remote address"
    exit 1
fi

cd ~/.task
mkdir -p ~/backups/tasks
tar czvf ~/backups/tasks/task-backup-$(date +'%Y%m%d').tar.gz ~/.task
rm -rf .git
git init
git commit -m 'Initial commit'
git remote add origin $1
git push --force --set-upstream origin master
