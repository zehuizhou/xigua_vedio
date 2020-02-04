#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020-02-03 12:16
# @Author  : July
import requests
from lxml import html
import csv
import os
import time
import random
from fake_useragent import UserAgent
from retrying import retry


ua = UserAgent(verify_ssl=False)


etree = html.etree

total_number = 5
proxy = {}

# 代理ip地址
proxy_url = 'http://route.xiongmaodaili.com/xiongmao-web/api/glip?secret=4ed5fac7b24bba823e18f5299a16232e&orderNo=GL20200112165156B8GF39F4&count=1&isTxt=0&proxyType=1'


@retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=5000)
def change_proxy(retry_count):
    if retry_count < 0:
        return

    result = requests.get(proxy_url).json()
    if result['msg'] == 'ok':
        ip = result['obj'][0]['ip']
        port = result['obj'][0]['port']
        proxies = {"http": "http://" + ip + ":" + port, "https": "http://" + ip + ":" + port}
        global proxy
        proxy = proxies
        print(f"代理ip为更改为：{proxies}")
        return proxies
    else:
        time.sleep(1)
        print('切换代理失败，重新尝试。。。')
        change_proxy(retry_count - 1)


def group_id_spider():
    index_url = 'https://m.ixigua.com/video/app/user/home/?to_user_id=4460305480&format=json&max_behot_time=1533027384'

    header = {
        'cookie': '_ga=GA1.2.1755011058.1580707999; _gid=GA1.2.267879450.1580707999; csrftoken=24ea48b55d179de7c12e90683c80355f; tt_webid=6789130846051747340; _ba=BA0.2-20200204-5138e-k0CQRONBrLKCP5SOKtKC; _gat_gtag_UA_100002932_27=1',
        'accept': 'application/json, text/plain, */*',
        'user-agent': ua.random,
    }
    ret = requests.get(url=index_url, headers=header).json()

    print(ret)
    video_list = ret['data']
    for video in video_list:
        group_id = video['group_id']
        with open('group_id.txt', 'a') as f:
            f.write(str(group_id) + '\n')


def comment_spider(offset=None, group_id=None):
    index_url = 'https://www.ixigua.com/tlb/comment/article/v5/tab_comments/'
    param = {
        'count': 10,
        'offset': offset,
        'group_id': group_id,
        'item_id': group_id
    }
    header = {
        'cookie': 'wafid=e9acd78d-b624-45e2-a0dc-9a555d2afbd6; wafid.sig=MNBK5tssmVyb68dHL-MjHjpN8bY; xiguavideopcwebid=6789089058868282891; xiguavideopcwebid.sig=g4uPDzl8lD0qNjB1ZZtXiGvQBDM; SLARDAR_WEB_ID=60689e23-b0bd-4b95-854e-e964462994ef; _ga=GA1.2.1755011058.1580707999; _gid=GA1.2.267879450.1580707999; s_v_web_id=k660shkd_xUiqO501_wisX_4SUh_87lb_voUp1MZ7OwPS; tt_webid=6789130846051747340',
        'accept': 'application/json, text/plain, */*',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }

    def get_ret(c):
        if c < 0:
            return
        try:
            ret = requests.get(url=index_url, headers=header, params=param, proxies=proxy, timeout=(3, 7)).json()
            return ret
        except:
            change_proxy(3)
            return get_ret(c-1)

    ret = get_ret(3)

    if offset == 0:
        global total_number
        total_number = ret['total_number']
        print(f'----------总页数{total_number}----------')

    print(ret)
    need_list = []
    data_list = ret['data']
    for data in data_list:
        title = ret['repost_params']['title']
        user_name = data['comment']['user_name']
        text = data['comment']['text']
        create_time = data['comment']['create_time']
        vedio_url = 'https://www.ixigua.com/i{}/'.format(group_id)
        timeArray = time.localtime(create_time)
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        need = [title, user_name, text, create_time, vedio_url]
        print(need)
        need_list.append(need)

    return need_list


def save_data(filename, data):
    if os.path.isfile(filename):
        is_exist = True
    else:
        is_exist = False
    with open(filename, "a", newline="", encoding="utf_8_sig") as f:
        c = csv.writer(f)
        if not is_exist:
            c.writerow(['标题', '评论人', '评论内容', '评论时间', '视频地址'])
        for line in data:
            c.writerow(line)


if __name__ == '__main__':
    # group_id_spider()

    with open('group_id.txt', 'r') as f:
        content = f.read().splitlines()
        group_id_list = content

    for group_id in group_id_list:
        data = comment_spider(offset=0, group_id=group_id)
        save_data('xigua.csv', data)

        for i in range(1, total_number//10+1):
            data = comment_spider(offset=i*10, group_id=group_id)
            save_data('xigua.csv', data)
            # time.sleep(random.uniform(1.1, 2))
            print('###############################')
            print(f'{group_id}第{i}保存成功')
            print('###############################')

