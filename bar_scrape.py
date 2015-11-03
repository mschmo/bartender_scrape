import os
import re
import requests
from BeautifulSoup import BeautifulSoup

from config import MAILGUN_API_KEY, MAILGUN_MESSAGE_URL


# Craigslist stuff
CRAIGSLIST_URL = 'http://philadelphia.craigslist.org'
BARTENDER_ENDPOINT = '/search/fbh?query=bartender'
# KEYWORDS = ('bartender', 'busser', 'runner', 'barback', 'bar back', 'dishwasher')
AREAS = ('philadelphia', 'center city', 'fairmount', 'art museum', 'northern liberties',
        'broad', 'grad.', 'hosp.', 'graduate', 'rittenhouse', 'cc', 'south street')


def bar_scrape():
    soup = BeautifulSoup(requests.get('{}{}'.format(CRAIGSLIST_URL, BARTENDER_ENDPOINT)).text)
    good_positions = []
    for position in soup.findAll('p', {'class': 'row'}):
        if already_posted(position['data-pid']):
            continue
        inner_text = position.contents[3].text.lower()
        location = re.search('\(([^()]+)\)', inner_text)
        if not location:
            continue
        location = location.group(0)
        if any([area in location for area in AREAS]):
            link = '{}{}'.format(CRAIGSLIST_URL, position.contents[1]['href'])
            good_positions.append({'title': inner_text, 'link': link, 'location': location})
    if good_positions:
        email_body = get_email_body(good_positions)
        return send_position_message(email_body, good_positions)


def send_position_message(body, jobs):
    data = {
        'from': 'mattschmo@gmail.com',
        'to': 'mattschmo@gmail.com',
        'subject': 'New Bartending Job ({})'.format(', '.join(set(job['location'].strip('()') for job in jobs))),
        'html': body
    }
    response = requests.post(MAILGUN_MESSAGE_URL, auth=('api', MAILGUN_API_KEY), data=data)
    return response.text


def already_posted(item_id):
    file_path = '{directory}/previous_posts.txt'.format(
        directory=os.path.dirname(os.path.abspath(__file__)))
    with open(file_path, 'r+') as f:
        posted_ids = [line.rstrip('\n') for line in f.readlines()]
        if item_id in posted_ids:
            return True
        f.write("{}\n".format(item_id))
        f.truncate()
    return False


def get_email_body(positions):
    return '<html><body><ul>{}</ul></body></html>'.format(
        ''.join(['<li><a href="{link}">{title}</a></li>'.format(
            link=position['link'], title=position['title']) for position in positions]))


if __name__ == '__main__':
    print(bar_scrape())
