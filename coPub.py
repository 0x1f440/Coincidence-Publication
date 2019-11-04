# -*- coding: utf-8 -*-

import re
import random
from flask import Flask, render_template, url_for, redirect
from requests_html import HTMLSession
from konlpy.tag import Kkma
from urllib.parse import quote
from base64 import urlsafe_b64decode, urlsafe_b64encode

app = Flask(__name__)
kkma = Kkma()
start_list = ["이것은 당신이 우연히 마주한 새로운 이야기의 시작입니다.",
              "새롭게 반짝거리는 먼지를 안경 너머로 바라보며 그는 한숨을 쉬었다.",
              "사실은 이 시작이 어떤 결말을 불러올 수 있는지 아무도 알지 못해요.",
              "그럼에도 불구하고 노력을 멈추지 않는 것이 버섯의 미덕이라고 생각합니다.",
              "폭풍이 올 것 같아요, 빨간 리본을 단 소녀가 말했지만 할머니는 듣지 못한 듯 뜨개질만 하고 있습니다."]


@app.route('/', defaults={'status': None})
@app.route('/<status>')


def index(status):
    if status is None:
        last_text = random.choice(start_list)
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
    r = session.get('http://www.yes24.com/searchcorner/Search?domain=BOOK&page_size=40&query=' + quote(keyword, encoding='cp949'))
    links = r.html.find('.goods_infogrp > .goods_name > a')
    random.shuffle(links)
    text = None

    for link in links:
        href = link.attrs['href']
        m = re.match(r'/Product/Goods/(\d+)', href)

        if m:
            print(m.group(1))
            text = get_first_text(m.group(1))
            if text is not None and kkma.nouns(text):
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
        content = r.html.find('.txtContentText', first=True).text
        m = re.match(r'.+?[.?!]', content).group(0)
        return m

    except:
        return None
