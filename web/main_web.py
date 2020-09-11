#!/usr/bin/python
# -*- coding:utf8 -*-
import os
import random
import re
import time
import urllib

import requests
from selenium import webdriver

# 账号配置文件
accountConfigPath = "./accountConfig.txt"
userConfigPath = "./userConfig.txt"

# ins 配置
insLoginURL = "https://www.instagram.com/accounts/login/"
insIndexURL = "https://www.instagram.com/"

class InsPaserHelper(object):

    def __init__(self, user_name, cookie=None):
        s = requests.session()
        s.keep_alive = False  # 关闭多余连接

        self.userName = user_name
        self.url = 'https://www.instagram.com/{}/'.format(user_name)
        self.headers = {
            'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
            'cookie': cookie
        }
        # 保存所有的图片和视频地址
        self.img_url_list = []
        # 这个uri有可能要根据不同的用户修改
        self.uri = 'https://www.instagram.com/graphql/query/?query_hash=f2405b236d85e8296cf30347c9f08c2a&variables=%7B%22id%22%3A%22{user_id}%22%2C%22first%22%3A12%2C%22after%22%3A%22{cursor}%22%7D'

        # 开始解析
        self.parse_html()

    def parse_html(self):
        print('====== 开始爬虫 ======')
        html_str = requests.get(url=self.url, headers=self.headers).text
        url_list = re.findall('''display_url":(.*?)\\u0026''', html_str)
        self.img_url_list.extend(url_list)
        # 获取用户id
        try:
            user_id = re.findall('"profilePage_([0-9]+)"', html_str, re.S)[0]
            print('用户id: ', user_id)
        except Exception as e:
            print(e)
        # 获取有值的cursor
        cursor_list = re.findall('"has_next_page":true,"end_cursor":(.*?)}', html_str, re.S)
        startCount = 1
        while len(cursor_list) > 0:
            try:
                print('** 开始第{}次 **'.format(startCount))
                next_page_url = self.uri.format(user_id=user_id, cursor=cursor_list[0]).replace('"', '')
                next_html_str = requests.get(next_page_url, headers=self.headers).text
                # 获取资源地址
                next_url_list = re.findall('''display_url":"(.*?)"''', next_html_str)
                video_list = re.findall('"video_url":(.*?),', next_html_str)
                if len(video_list) > 0:
                    next_url_list.extend(video_list)
                self.img_url_list.extend(next_url_list)
                cursor_list = re.findall('"has_next_page":true,"end_cursor":(.*?)}', next_html_str, re.S)
                time.sleep(random.randint(1, 2))
                startCount = startCount + 1
            except Exception as e:
                print(e)
                break
        self.img_url_list = list(set(self.img_url_list))
        print('** 总资源数量: {count} **'.format(count=len(self.img_url_list)))
        print('** 开始启动下载程序 **')
        for index in range(len(self.img_url_list)):
            url = self.img_url_list[index]
            self.saveSimple(url)
    print('** 全部下载完成 **')
    print('====== 结束爬虫 ======')

    # 简单的下载封装
    def saveSimple(self, downUrl):
        # 开始下载图片，生成文件夹再下载
        dirpath = './{}'.format(self.userName)
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        print('**> 开始下载:{}'.format(downUrl))
        try:
            response = requests.get(downUrl, headers=self.headers, timeout=10)
            if response.status_code == 200:
                content = response.content
                # 判断后缀
                endw = 'mp4' if r'mp4?_nc_ht=scontent-nrt1-1.cdninstagram.com' in downUrl else 'jpg'
                file_path = r'./{path}/{name}.{jpg}'.format(path=self.userName,
                                                            name='%04d' % random.randint(0, 9999),
                                                            jpg=endw)
                with open(file_path, 'wb') as f:
                    f.write(content)
                    f.close()
            else:
                print('** 下载异常 ** ')
        except Exception as e:
            print(e)

class InsSpider:
    def __init__(self):
        if self.onInitAccountInfo() == 0:
            self.onInitUserInfo()
            print("完成基本初始化信息...")
            if self.users is not None and len(self.users) > 0:
                print("*" * 100)
                print("== 开始启动爬虫 ==")
                self.onInitDriver()
                self.onInsDisplayCookie()
                self.onPaser()
            else:
                print("基本初始化信息错误...")
        else:
            print("基本初始化信息错误...")
        pass

    # 随机睡眠 1-5
    def some_sleep(self):
        time.sleep(random.randint(1, 2))

    def onInitAccountInfo(self):
        print("== 读取登录账号密码 ==")
        accountConfig = open(accountConfigPath).read().split(",")
        if len(accountConfig) == 2:
            self.account = accountConfig[0]
            self.password = accountConfig[1]
            print("== 读取账号:{account},密码:{password} ==".format(account=self.account, password=self.password))
            return 0
        return 1

    def onInitUserInfo(self):
        print("== 读取爬虫用户 ==")
        userConfig = open(userConfigPath).read().split(",")
        self.users = userConfig
        print("== 读取用户数:{} ==".format(len(self.users)))

    def onInitDriver(self):
        self.webdriver = webdriver.Chrome()
        self.cookies = ""

    def onInsDisplayCookie(self):
        self.webdriver.get(insLoginURL)
        # 获取登录组件
        self.some_sleep()
        btn_login = self.webdriver.find_element_by_class_name("sqdOP")
        username_input = self.webdriver.find_element_by_name("username")
        password_input = self.webdriver.find_element_by_name("password")
        print("**> 开始输入登录信息...")
        username_input.clear()
        # 写入账号
        username_input.send_keys(self.account)
        password_input.clear()
        # 写入密码
        password_input.send_keys(self.password)
        self.some_sleep()
        print("**> 开始登录...")
        btn_login.click()
        time.sleep(10)
        # 返回当前界面的url
        curpage_url = self.webdriver.current_url
        print("**> 当前进入的网页{}".format(curpage_url))
        cookie = [
            item['name'] + '=' + item['value']
            for item in self.webdriver.get_cookies()
        ]
        for value in cookie:
            self.cookies += value + ';'
        print("**> 获取到cookie -> ", self.cookies)
        self.some_sleep()
        self.webdriver.get(insIndexURL)
        pass

    def onPaser(self):
        for username in self.users:
            userUrl = insIndexURL + username + "/"
            self.webdriver.get(userUrl)
            self.some_sleep()
            # 代理helper进行解析
            InsPaserHelper(username,self.cookies)

spider = InsSpider()
