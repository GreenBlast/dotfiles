#!/bin/bash

BACKUP_LOCATION=~/backup
TASK_DIR_LOCATION=~/.task
PKI_LOCATION=/usr/share/taskd/pki

export TASKDATA=/var/lib/taskd

echo "Backup current tasks"
mkdir -p $BACKUP_LOCATION

tar cvaf $BACKUP_LOCATION/task-$(date -u +"%Y-%m-%d-%H-%M-%SZ").tar.gz $TASK_DIR_LOCATION/*

echo "Generating server certs"

cd $PKI_LOCATION
sudo ./generate

echo "Generating client certs"
sudo ./generate.client Greenblast

echo "Copying server certs"
sudo cp ca.cert.pem ca.key.pem client.cert.pem client.key.pem server.cert.pem server.crl.pem server.key.pem $TASKDATA/pki/

echo "Copying client certs"
sudo cp ca.cert.pem Greenblast.cert.pem Greenblast.key.pem $TASK_DIR_LOCATION/


echo "Restarting taskd"
sudo systemctl restart taskd

#scp -r pi@192.168.3.175:/home/pi/.task/\{ca.cert.pem,Greenblast.cert.pem,Greenblast.key.pem\} ~/.task/
# /Users/user/Library/Android/sdk/platform-tools/adb push ~/.task/ca.cert.pem "/sdcard/android/data/com.taskwc2/files/e20729e9-36f1-4ba6-9153-2a04d7b14d2a/"
# /Users/user/Library/Android/sdk/platform-tools/adb push ~/.task/Greenblast.cert.pem "/sdcard/android/data/com.taskwc2/files/e20729e9-36f1-4ba6-9153-2a04d7b14d2a/"
# /Users/user/Library/Android/sdk/platform-tools/adb push ~/.task/Greenblast.key.pem "/sdcard/android/data/com.taskwc2/files/e20729e9-36f1-4ba6-9153-2a04d7b14d2a/"
