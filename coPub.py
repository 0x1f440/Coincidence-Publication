import re
from flask import Flask,  render_template, url_for, request, redirect
from requests_html import HTMLSession
from konlpy.tag import Kkma
from urllib.parse import quote
from base64 import urlsafe_b64decode, urlsafe_b64encode

app = Flask(__name__)


@app.route('/', defaults={'status': None})
@app.route('/<status>')
def index(status):
    kkma = Kkma()

    if status is None:
        last_text = get_first_text(4564384)
        return redirect(url_for('.index', status=urlsafe_b64encode(last_text.encode())))

    t = urlsafe_b64decode(status).decode().split('|')
    text = ''
    if len(t) > 1:
        text = t[0]
    last_text = t[-1]

    status = urlsafe_b64encode((text + ' ' + last_text).encode())

    nouns = kkma.nouns(last_text)
    for noun in nouns:
        if not is_number(noun):
            url = url_for('.search', status=status, keyword=noun)
            last_text = last_text.replace(noun, '<a class="nouns" href="{}">{}</a>'.format(url, noun))

    return render_template('index.html', text=text, last_text=last_text)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


@app.route('/search/<status>/<keyword>')
def search(status, keyword):
    session = HTMLSession()
    r = session.get('http://www.yes24.com/searchcorner/Search?domain=BOOK&page_size=120&query=' + quote(keyword, encoding='cp949'))
    links = r.html.find('.goods_infogrp > .goods_name > a')
    book_ids = []
    for link in links:
        href = link.attrs['href']
        m = re.match(r'/24/goods/(\d+)', href)
        if m:
            book_ids.append(m.group(1))
    text = None
    for book_id in book_ids:
        text = get_first_text(book_id)
        if text is not None:
            break

    if text is None:
        text = "사실 당신의 이야기는 여기서 끝이지만, 마주한 끝은 새로운 시작이 되기도 합니다."
    current = urlsafe_b64decode(status).decode()
    current += '|' + text
    return redirect(url_for('.index', status=urlsafe_b64encode(current.encode())))


def get_first_text(book_id):
    try:
        session = HTMLSession()
        r = session.get('http://www.yes24.com/24/goods/{}'.format(book_id))
        content = r.html.find('#contents_inside', first=True).text
        m = re.match(r'.+?[.?!]', content)

        return m.group(0)
    except:
        return None
