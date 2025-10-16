docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
echo y | docker network prune
echo y | docker volume prune