import requests
import re
import time
import random
import os
import click
import csv
import datetime

myCookie = ""


@click.command()
@click.option('-n', "--name", type=str, default=None, help="用户昵称id")
@click.option('-d', "--dir", type=str, default=None, help="保存路径")
@click.option('-ns', "--names", type=str, default=None, help="多个用户id")
def main(name, dir, names):
    nameResult = "petparadise_official"
    dirResult = "."
    namesResult = []
    if dir is not None:
        dirResult = dir
        pass
    if name is not None:
        nameResult = name
        pass
    if names is not None:
        namesResult = names
        pass

    namesResult = namesResult.split(",")
    if (len(namesResult) > 0):
        print("== 多个用户抓取 ==")
        # 提前构建文件夹存储
        now = datetime.datetime.now()
        dir = "./mult/{today}_{hour}:{min}".format(today=datetime.date.today(), hour=now.hour, min=now.minute)
        if not os.path.exists(dir):
            os.makedirs(dir)
        # 开始遍历抓取,单线程执行
        for i in range(len(namesResult)):
            readyName = namesResult[i]
            print("** 开始抓取用户 {} **".format(readyName))
            InstaSpider(readyName, dirResult, myCookie, dir)

    else:
        print("== 单个用户抓取 ==")
        InstaSpider(nameResult, dirResult, myCookie)


class InstaSpider(object):

    def __init__(self, user_name, path_name=None, cookie=None, dir=None):
        # 初始化要传入ins用户名和保存的文件夹名
        self.path_name = path_name if path_name else user_name
        # 不能多余链接
        s = requests.session()
        s.keep_alive = False  # 关闭多余连接

        # self.url = 'https://www.instagram.com/real__yami/'
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

        if (dir is None):
            now = datetime.datetime.now()
            dir = "./{today}_{hour}:{min}".format(today=datetime.date.today(), hour=now.hour, min=now.minute)
            if not os.path.exists(dir):
                os.mkdir(dir)
        # 开始解析
        self.parse_html(dir)

    def parse_html(self, dir):
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
        self.display_source(dir)
        print('====== 结束爬虫 ======')

    def display_source(self, dir):
        with open("./{dir}/{name}.csv".format(dir=dir, name=self.userName), "w") as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(["昵称:"])
            writer.writerow(["{name}".format(name=self.userName)])
            writer.writerow(["用户主页:"])
            writer.writerow(["https://www.instagram.com/{name}/".format(name=self.userName)])
            writer.writerow(["图片or视频链接:"])
            for i in range(len(self.img_url_list)):
                print('** 正在整理{0}张：'.format(i), '资源，还剩{0}张 **'.format(len(self.img_url_list) - i - 1))
                downUrl = self.img_url_list[i].replace('"', '')
                # self.download(self.img_url_list[i].replace('"', '')) # 下载
                print('** 开始写入excel **')
                writer.writerow([downUrl])
        pass

    def download(self, downUrl):
        # 开始下载图片，生成文件夹再下载
        dirpath = './{}'.format(self.userName)
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        print('** 开始下载 ** ')
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
                    print('** 下载完成 ** ')
                    f.write(content)
                    f.close()
            else:
                print('** 下载异常 ** ')
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
