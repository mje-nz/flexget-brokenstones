# Flexget BrokenStones automation
BrokenStones lookup plugin for FlexGet, which looks up items from one of the RSS feeds and adds these fields:

* `freeleech`
* `neutral_leech`
* `snatched`
* `content_size` (in MB)
* `snatches`
* `seeders`
* `leechers`

See [config.yml](config.yml) for a usage example. 

To install:

```bash
docker run -d \
  -e PGID=1000 -e PUID=1000 -e TZ=Pacific/Auckland \
  -p 5050:5050 \
  -e WEB_PASSWD="admin 1 2 3" \
  -e FLEXGET_LOG_LEVEL=verbose \
  -v $(pwd):/config \
  --name=flexget --restart=unless-stopped \
  cpoppema/docker-flexget
```

If you delete the database you'll have to reset your web UI password:

```bash
docker exec -it flexget bash
flexget -c /config/config.yml web passwd "admin 1 2 3"
```
