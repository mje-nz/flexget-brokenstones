"""BrokenStones plugin for FlexGet."""
from __future__ import unicode_literals, division, absolute_import
from builtins import *
from future.standard_library import install_aliases
install_aliases()

import logging
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from flexget import plugin
from flexget.event import event
from flexget.utils.requests import TimedLimiter, RequestException
from flexget.utils.requests import Session as RequestSession


BASE_URL = 'brokenstones.club'
log = logging.getLogger('brokenstones')
requests = RequestSession()
requests.add_domain_limiter(TimedLimiter(BASE_URL, '2 seconds'))


def login():
    data = {
        'username': <username>,
        'password': <password>,
        'keeplogged': '1'
    }
    login_url = 'https://' + BASE_URL + '/login.php'
    r = requests.post(login_url, data=data)
    if r.url == login_url:
        raise plugin.PluginError('Failed to log in')


def get_comments(entry):
    try:
        return requests.get(entry['comments'])
    except RequestException as e:
        log.error('Error while fetching page: %s' % e)
        return


def get_id(url):
    return parse_qs(urlparse(url).query)['id']


class BrokenStones(object):
    def on_task_filter(self, task, config):
        for entry in task.entries:
            log.info('Checking ' + entry['url'])
            r = get_comments(entry)
            if r.url.endswith('login.php'):
                login()
                r = get_comments(entry)
                if r.url.endswith('login.php'):
                    raise plugin.PluginError('Login appeared to succeed but next request failed')
            html = r.content
            soup = BeautifulSoup(html, 'lxml')
            expected_id = get_id(entry['url'])
            for el in soup.select('tr.torrent_row'):
                dl_url = el.find('a', string='DL')['href']
                log.debug('Comparing ' + dl_url)
                if get_id(dl_url) == expected_id:
                    # Found the link we're here for
                    if el.find('strong', string='Freeleech!'):
                        # It's freeleech, download it
                        entry.accept(remember=True)
                    else:
                        entry.reject('Not freeleech', remember=True)
                        break
            else:
                log.error('Could not match download link in page')


@event('plugin.register')
def register_plugin():
    plugin.register(BrokenStones, 'brokenstones', api_ver=2)
