#!/bin/sh

if [ "$(id -u)" != "0" ]; then
    RUN_AS_ROOT='sudo'
else
    RUN_AS_ROOT=''
fi

# If no old permissions file
if [ ! -f "${1}.old_permissions"  ]; then
# Save old permissions
$RUN_AS_ROOT stat -c%U:%G $1 > "${1}.old_permissions"
$RUN_AS_ROOT chmod +r "${1}.old_permissions"

# Changing permissions
$RUN_AS_ROOT chown $2:$2 $1
else
# Read old permissions
old_permissions="$(cat ${1}.old_permissions)"

# Changing permissions
$RUN_AS_ROOT chown ${old_permissions} ${1}

# Deleting old permissions file
$RUN_AS_ROOT rm -f ${1}.old_permissions

fi

