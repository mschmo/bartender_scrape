import os
import re
import requests
from BeautifulSoup import BeautifulSoup

from config import MAILGUN_API_KEY, MAILGUN_MESSAGE_URL


# Craigslist stuff
BARTENDER_URL = 'http://philadelphia.craigslist.org/search/fbh?query=bartender'
# KEYWORDS = ('bartender', 'busser', 'runner', 'barback', 'bar back', 'dishwasher')
AREAS = ('philadelphia', 'center city', 'fairmount', 'art museum', 'northern liberties',
        'broad', 'grad.', 'hosp.', 'graduate', 'temple', 'rittenhouse')

def bar_scrape():
    soup = BeautifulSoup(requests.get(BARTENDER_URL).text)
    good_positions = []
    for position in soup.findAll('p', {'class': 'row'}):
        position_id = position['data-pid']
        if already_posted(position_id):
            continue
        inner_text = position.contents[3].text.lower()
        location = re.search('\(([^()]+)\)', inner_text)
        if not location:
            continue
        location = location.group(0)
        for area in AREAS:
            if area in location:
                link = 'http://philadelphia.craigslist.org{}'.format(position.contents[1]['href'])
                good_positions.append({'title': inner_text, 'link': link})
                break
    if good_positions:
        email_body = get_email_body(good_positions)
        return send_position_message(email_body)

def send_position_message(body):
    data = {
        'from': 'mattschmo@gmail.com',
        'to': 'mattschmo@gmail.com',
        'subject': 'New Bartending Position',
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
    bar_scrape()