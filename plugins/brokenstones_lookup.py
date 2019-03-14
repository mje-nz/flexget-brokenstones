"""BrokenStones plugin for FlexGet.

I don't know how to use FlexGet, so this is pretty rough.

Author: Matthew Edwards
Date: March 2019
"""

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
log = logging.getLogger('brokenstones_lookup')
requests = RequestSession()
requests.add_domain_limiter(TimedLimiter(BASE_URL, '2 seconds'))


def login(username, password):
    data = {
        'username': username,
        'password': password,
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


# https://stackoverflow.com/a/42865957
units = {"B": 1, "KB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12}
def parse_size(size):
    number, unit = [string.strip() for string in size.split()]
    return int(float(number)*units[unit])


class BrokenStonesLookup(object):
    """BrokenStones lookup plugin."""

    schema = {
        'type': 'object',
        'properties': {
            'username': {'type': 'string'},
            'password': {'type': 'string'},
        },
        'required': ['username', 'password'],
        'additionalProperties': False,
    }

    # Should really use on_task_metainfo, but this way remember_rejected goes first
    def on_task_filter(self, task, config):
        for entry in task.entries:
            log.info('Checking {} ({})'.format(entry['title'], entry['url']))
            r = get_comments(entry)
            if r.url.endswith('login.php'):
                login(config['username'], config['password'])
                r = get_comments(entry)
                if r.url.endswith('login.php'):
                    raise plugin.PluginError('Login appeared to succeed but next request failed')
            if 'log.php' in r.url:
                entry.reject('torrent removed', remember=True)
            html = r.content
            soup = BeautifulSoup(html, 'lxml')
            expected_id = get_id(entry['url'])
            for el in soup.select('tr.torrent_row'):
                dl_url = el.find('a', string='DL')['href']
                log.debug('Comparing ' + dl_url)
                if get_id(dl_url) == expected_id:
                    # Found the link we're here for

                    if el.find('strong', string='Freeleech!'):
                        log.info('Is freeleech')
                        entry['freeleech'] = True
                    else:
                        entry['freeleech'] = False

                    if el.find('strong', string='Neutral Leech!'):
                        log.info('Is neutral leech')
                        entry['neutral_leech'] = True
                    else:
                        entry['neutral_leech'] = False

                    if el.find('strong', string='Snatched!'):
                        log.info('Is snatched')
                        entry['snatched'] = True
                    else:
                        entry['snatched'] = False

                    entry['content_size'] = parse_size(el.find_all('td')[1].string)
                    entry['snatches'] = el.find_all('td')[2].string
                    entry['seeders'] = el.find_all('td')[3].string
                    entry['leechers'] = el.find_all('td')[4].string
                    log.info('Size: {}, snatches: {}, seeders: {}, leechers: {}'.format(
                             entry['content_size'], entry['snatches'], entry['seeders'], entry['leechers']))
                    break
            else:
                # This happens when a new release is taken down.  It might come back (e.g.,
                # if there was a problem and then the problem is fixed), so don't remember
                # this rejection.
                entry.reject('could not match download link in page')


@event('plugin.register')
def register_plugin():
    plugin.register(BrokenStonesLookup, 'brokenstones_lookup', api_ver=2)
