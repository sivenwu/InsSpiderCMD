import requests
import re
import time
import random
import os
import click
import csv

myCookie = ""


@click.command()
@click.option('-n', "--name", type=str, default=None, help="用户昵称id")
@click.option('-d', "--dir", type=str, default=None, help="保存路径")
def main(name, dir):
    nameResult = "petparadise_officials"
    dirResult = "."
    if dir is not None:
        dirResult = dir
        pass
    if name is not None:
        nameResult = name
        pass
    InstaSpider(nameResult, dirResult, myCookie)


class InstaSpider(object):

    def __init__(self, user_name, path_name=None, cookie=None):
        # 初始化要传入ins用户名和保存的文件夹名
        self.path_name = path_name if path_name else user_name
        # 不能多余链接
        s = requests.session()
        s.keep_alive = False  # 关闭多余连接

        # self.url = 'https://www.instagram.com/real__yami/'
        self.url = 'https://www.instagram.com/{}/'.format(user_name)
        self.headers = {
            'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
            'cookie': cookie
        }
        # 保存所有的图片和视频地址
        self.img_url_list = []
        # 这个uri有可能要根据不同的用户修改
        self.uri = 'https://www.instagram.com/graphql/query/?query_hash=f2405b236d85e8296cf30347c9f08c2a&variables=%7B%22id%22%3A%22{user_id}%22%2C%22first%22%3A12%2C%22after%22%3A%22{cursor}%22%7D'
        self.parse_html()

    def parse_html(self):
        print(self.url)
        print(self.headers)
    # 获取信息:刚开始的12条图片,id,cursor
        html_str = requests.get(url=self.url, headers=self.headers).text
        # print(html_str)
    # 获取12条图片地址
        url_list = re.findall('''display_url":(.*?)\\u0026''', html_str)
        print(len(url_list))
        self.img_url_list.extend(url_list)
        # 获取用户id
        try:
            user_id = re.findall('"profilePage_([0-9]+)"', html_str, re.S)[0]
            print('用户id', user_id)
        except Exception as e:
            print('获取用户id失败')
            print(e)
        # 获取有值的cursor
        cursor_list = re.findall('"has_next_page":true,"end_cursor":(.*?)}', html_str, re.S)
        while len(cursor_list) > 0:
            # 默认访问12张图片
            try:
                next_page_url = self.uri.format(user_id=user_id, cursor=cursor_list[0]).replace('"', '')
                print(next_page_url)
                next_html_str = requests.get(next_page_url, headers=self.headers).text
                # 获取12条图片地址
                next_url_list = re.findall('''display_url":"(.*?)"''', next_html_str)
                video_list = re.findall('"video_url":(.*?),', next_html_str)
                if len(video_list) > 0:
                    next_url_list.extend(video_list)
                self.img_url_list.extend(next_url_list)
                cursor_list = re.findall('"has_next_page":true,"end_cursor":(.*?)}', next_html_str, re.S)
                print(len(cursor_list))
                time.sleep(random.random())
            except Exception as e:
                print(e)
                break
        print(len(self.img_url_list))
        print(self.img_url_list)
        self.img_url_list = list(set(self.img_url_list))
        print('去重后', len(self.img_url_list))
        # self.download_img()
        #先写入columns_name
        with open("test.csv","w") as csvfile:
            writer = csv.writer(csvfile)
            #先写入columns_name
            writer.writerow(["测试"])
            #写入多行用writerows
            for i in range(len(self.img_url_list)):
                try:
                    # writer.writerow(self.img_url_list[i])
                    print(self.img_url_list[i])
                except Exception as e:
                    print(e)

    def download_img(self):
        # 开始下载图片，生成文件夹再下载
        dirpath = '/Users/paul/Desktop/{}'.format(self.path_name)
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        for i in range(len(self.img_url_list)):
            print('\n正在下载第{0}张：'.format(i), '还剩{0}张'.format(len(self.img_url_list) - i - 1))
            try:
                response = requests.get(self.img_url_list[i].replace('"', ''), headers=self.headers, timeout=10)
                if response.status_code == 200:
                    content = response.content
                    # 判断后缀
                    endw = 'mp4' if r'mp4?_nc_ht=scontent.cdninstagram.com' in self.img_url_list[i] else 'jpg'
                    file_path = r'/Users/paul/Desktop/{path}/{name}.{jpg}'.format(path=self.path_name,
                                                                                  name='%04d' % random.randint(0, 9999),
                                                                                  jpg=endw)
                    with open(file_path, 'wb') as f:
                        print('第{0}张下载完成： '.format(i))
                        f.write(content)
                        f.close()
                else:
                    print('请求照片二进制流错误, 错误状态码：', response.status_code)
            except Exception as e:
                print(e)


if __name__ == '__main__':
    main()
