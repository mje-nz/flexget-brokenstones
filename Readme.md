# Flexget BrokenStones automation

To install:

```bash
docker run -d \
  -e PGID=1000 -e PUID=1000 -e TZ=Pacific/Auckland \
  -p 5050:5050 \
  -e WEB_PASSWD="admin 1 2 3" \
  -v $(pwd):/config \
  --name=flexget --restart=unless-stopped \
  cpoppema/docker-flexget
```
