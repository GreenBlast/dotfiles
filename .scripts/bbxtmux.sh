#!/bin/bash
# tmux \
#     new-window 'tail -F -n 150 /var/log/fides/sniffer.log' \; \
#     rename-window 'bbx_logs' \; \
#     split-window 'tail -F -n 150 /var/log/fides/sniffer-stats.log'

# tmux \
#tmux new-window \; \
##	rename-window 'up and down service' \; \
##	new-window  'sudo vim /etc/fides/fides-sniffer.config' \; \
##	rename-window 'bbx configuration' \; \
##	new-window  'sudo vim /etc/fides/fides-sniffer.protocol.config' \; \
##	rename-window 'protocol configuration' \; \
#    new-window 'bash -s < tail -F -n 150 /var/log/fides/sniffer.log' \; \
#    rename-window 'bbx_logs' \; \
#    split-window 'tail -F -n 150 /var/log/fides/sniffer-stats.log'


#tmux new-window "bash --rcfile <(echo '. ~/.bashrc; tail -F -n 150 /var/log/fides/sniffer.log')"\; \
#    rename-window 'bbx_logs' \; \
#    split-window "bash --rcfile <(echo '. ~/.bashrc; tail -F -n 150 /var/log/fides/sniffer-stats.log')"


tmux split-window "bash --rcfile <(echo '. ~/.bashrc; tail -F -n 150 /var/log/fides/sniffer-stats.log')" \;\
    rename-window 'bbx_logs'
tail -F -n 150 '/var/log/fides/sniffer.log'

