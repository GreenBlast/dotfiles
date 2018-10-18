sudo /usr/local/nginx/sbin/nginx
omxplayer -g  -o hdmi -r --live rtmp://localhost:1935/live
sudo /usr/local/nginx/sbin/nginx -s stop

