# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import re
import sys
from collections import OrderedDict
from urllib.parse import urlencode, parse_qsl

import urllib3
import xbmc
import xbmcgui
import xbmcplugin
# from html.parser import HTMLParser
from bs4 import BeautifulSoup

_url = sys.argv[0]
_handle = int(sys.argv[1])

FEEDS = OrderedDict([
    ('Spravodajstvo', 'http://www.tvpovazie.sk/index.php/videoarchiv-3/archivspravodajstvo2'),
    ('Šport', 'http://www.tvpovazie.sk/index.php/videoarchiv-3/sport'),
    ('Na považí', 'http://www.tvpovazie.sk/index.php/videoarchiv-3/na-povazi'),
    ('Na rovinu', 'http://www.tvpovazie.sk/index.php/videoarchiv-3/na-rovinu'),
    ('VÚC', 'http://www.tvpovazie.sk/index.php/videoarchiv-3/vuc'),
    ('Záznamy', 'http://www.tvpovazie.sk/index.php/videoarchiv-3/zaznamy'),
    ('Dubnický Magazín', 'http://www.tvpovazie.sk/index.php/videoarchiv-3/dubnicky-magazin'),
    ('Púchovský Magazín', 'http://www.tvpovazie.sk/index.php/videoarchiv-3/puchovsky-magazin'),
    ('My, Vy, Oni', 'http://www.tvpovazie.sk/index.php/videoarchiv-3/my-vy-oni')
])






def search(page):
    user_agent = {'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"}
    http = urllib3.PoolManager(1, headers=user_agent)
    return http.request("GET", page).data.decode("utf-8")


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    xbmcplugin.setContent(_handle, 'videos')
    for category in FEEDS.keys():
        list_item = xbmcgui.ListItem(label=category)
        url = get_url(action='listing', url=FEEDS[category])
        # is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    # xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.endOfDirectory(_handle)


def list_videos(url):
    """
    Create the list of playable videos in the Kodi interface.

    :param url: Url to video directory
    :type url: str
    """
    httpdata = search(url)
    raw_html_data = BeautifulSoup(httpdata, "html.parser").find_all("div", class_="catItemImageBlock")
    # parser=HTMLParser()
    for (data) in raw_html_data:
        title_data = data.find("a")
        title = title_data["title"]
        relation_url = title_data["href"]
        relation_img = title_data.find("img")["data-original"]
        relation_img = "http://www.tvpovazie.sk" + relation_img
        relation_url = "http://www.tvpovazie.sk" + str(relation_url)
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=title)
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': title,
                                    'mediatype': 'video'})
        list_item.setArt({'thumb': relation_img, 'icon': relation_img, 'fanart': relation_img})
        list_item.setProperty('IsPlayable', 'true')
        url = get_url(action='play', video=relation_url)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    # next = re.search(r'<a class="next page-numbers" href="(\S*?)"', httpdata)
    # if next:
    #     url = get_url(action='listing', url=next.group(1))
    #     is_folder = True
    #     xbmcplugin.addDirectoryItem(_handle, url, xbmcgui.ListItem(label='Ďalšie'), is_folder)

    xbmcplugin.endOfDirectory(_handle)


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # get video link
    html = search(path)
    if html:
        # videolink = BeautifulSoup(html, "html.parser").find("video")["src"]
        # xbmc.log(videolink)
        pattern = r"'file':\s*'(http[^\']+)'"
        url_match = re.search(pattern, html)
        videolink= url_match.group(1)
        play_item = xbmcgui.ListItem(path=videolink)
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of videos
            list_videos(params['url'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
