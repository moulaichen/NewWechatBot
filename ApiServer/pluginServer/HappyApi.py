import os

from PIL import Image
from bs4 import BeautifulSoup

import FileCache.FileCacheServer as Fcs
import Config.ConfigServer as Cs
from OutPut.outPut import op
import requests
import random
import time


def convert_coordinates(coord):
    lat, lon = coord.split()

    if float(lat) > 90:
        lat, lon = lon, lat

    lat = lat + "N"
    lon = lon + "E"
    return f"{lat}{lon}"


def get_images_from_folder(folder_path):
    images = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif')):
            img_path = os.path.join(folder_path, file_name)
            img = Image.open(img_path)
            images.append(img)
    return images


def resize_images(images, size):
    resized_images = []
    for img in images:
        resized_images.append(img.resize(size, Image.LANCZOS))
    return resized_images


def concatenate_images(images, images_per_row, size):
    num_images = len(images)
    total_width = images_per_row * size[0]
    rows = (num_images + images_per_row - 1) // images_per_row  # 计算行数
    total_height = rows * size[1]

    new_image = Image.new('RGB', (total_width, total_height))
    for index, img in enumerate(images):
        x_offset = (index % images_per_row) * size[0]
        y_offset = (index // images_per_row) * size[1]
        new_image.paste(img, (x_offset, y_offset))

    return new_image


class HappyApi:
    def __init__(self):
        """
        不要直接调用此类
        娱乐功能Api文件
        """
        # 读取配置文件
        configData = Cs.returnConfigData()
        self.txKey = configData['apiServer']['apiConfig']['txKey']
        self.picUrlList = configData['apiServer']['picApi']
        self.videoUrlList = configData['apiServer']['videosApi']
        self.dogApi = configData['apiServer']['dogApi']
        self.fishApi = configData['apiServer']['fishApi']
        self.kfcApi = configData['apiServer']['kfcApi']

    def downloadFile(self, url, savePath):
        """
        通用下载文件函数
        :param url:
        :param savePath:
        :return:
        """
        try:
            content = requests.get(url, timeout=30, verify=True).content
            with open(savePath, mode='wb') as f:
                f.write(content)
            return savePath
        except Exception as e:
            op(f'[-]: 通用下载文件函数出现错误, 错误信息: {e}')
            return None

    def getPic(self, ):
        """
        美女图片下载
        :return:
        """
        op(f'[*]: 正在调用美女图片Api接口... ...')
        picUrl = random.choice(self.picUrlList)
        savePath = Fcs.returnPicCacheFolder() + '/' + str(int(time.time() * 1000)) + '.jpg'
        picPath = self.downloadFile(picUrl, savePath)
        if not picPath:
            for picUrl in self.picUrlList:
                picPath = self.downloadFile(picUrl, savePath)
                if picPath:
                    break
                continue
        return picPath

    def getHuPu(self, ):
        """
        虎扑
        :return:
        """
        op(f'[*]: 正在调用虎扑热搜API接口... ...')
        url = "https://api.vvhan.com/api/hotlist/huPu"
        try:
            json_data = requests.get(url=url, timeout=30, verify=False).json()
            if json_data['success'] is False:
                msg = f'[~]: 虎扑热搜接口出现错误, 错误信息请查看日志 ~~~~~~'
                return msg
            hot_search = json_data['data']
            if not hot_search:
                return None

            content_lst = []
            queue1 = hot_search[:len(hot_search) // 2]
            queue2 = hot_search[len(hot_search) // 2:]
            # 分别处理两个队列
            for i, queue_data in enumerate([queue1, queue2]):
                start_index = i * (len(hot_search) // 2)
                end_index = start_index + len(queue_data)
                content = f'虎扑热搜 {start_index + 1}-{end_index}\n'
                for index, item in enumerate(queue_data):
                    content += f'{start_index + index + 1}、{item["title"]}\n{item["url"]}\n'
                content_lst.append(content)
            op(f'[*]: 虎扑热搜API接口调用成功... ...')
            return content_lst
        except Exception as e:
            msg = f'[-]: 虎扑热搜接口出现错误, 错误信息：{e}'
            op(msg)

    def getImageAll(self, ):
        """
        图片整合
        :return:
        """
        op(f'[*]: 正在整合图片... ...')
        savePath = Fcs.returnAllImageCacheFolder() + '/' + str(int(time.time() * 1000)) + '.jpg'
        folder_path = Fcs.returnAllImageQunCacheFolder() + '/'
        image_size = (1000, 1500)
        images_per_row = 3
        try:
            images = get_images_from_folder(folder_path)
            resized_images = resize_images(images, image_size)
            result_image = concatenate_images(resized_images, images_per_row, image_size)
            result_image.save(savePath)
        except Exception as e:
            msg = f'[-]: 整合图片出现错误, 错误信息：{e}'
            savePath = self.getImageAll()
            op(msg)
        return savePath

    def getWeatherImage(self, content):
        """
        天气
        :return:
        """
        op(f'[*]: 正在搜天气... ...')
        savePath = Fcs.returnWeatherCacheFolder() + '/' + str(int(time.time() * 1000)) + '.jpg'
        try:
            image_data = self.select_weather_image(content)
            if image_data is None:
                op(f'[*]: 图片下载失败... ...')
            with open(savePath, 'wb') as f:
                f.write(image_data)
        except Exception as e:
            msg = f'[-]: 搜天气出现错误, 错误信息：{e}'
            savePath = self.getWeatherImage(content)
            op(msg)
        return savePath

    @staticmethod
    def select_weather_image(content):
        latitude = convert_coordinates(content)
        base_url = 'https://www.meteoblue.com/en/weather/week/'
        coordinates = f'{latitude}'
        url = f'{base_url}{coordinates}'

        # 发起请求并获取页面内容
        response = requests.get(url)
        html_content = response.content

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # 查找所有包含图片的div标签
        image_div = soup.find('div', class_='bloo meteogram-scrollable')

        img_data = ""
        if image_div:
            img_url = image_div.find('img')['data-original']
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            # 下载图片
            img_data = requests.get(img_url).content

        return img_data

    def getVideo(self, ):
        """
        美女视频下载
        :return:
        """
        op(f'[*]: 正在调用美女视频Api接口... ...')
        videoUrl = random.choice(self.videoUrlList)
        savePath = Fcs.returnVideoCacheFolder() + '/' + str(int(time.time() * 1000)) + '.mp4'
        videoPath = self.downloadFile(videoUrl, savePath)
        if not videoPath:
            for videoUrl in self.videoUrlList:
                videoPath = self.downloadFile(videoUrl, savePath)
                if videoPath:
                    break
                continue
        return videoPath

    def getFish(self, ):
        """
        摸鱼日历下载
        :return:
        """
        op(f'[*]: 正在调用摸鱼日历Api接口... ...')
        savePath = Fcs.returnPicCacheFolder() + '/' + str(int(time.time() * 1000)) + '.jpg'
        fishPath = self.downloadFile(url=self.fishApi, savePath=savePath)
        if not fishPath:
            for i in range(2):
                fishPath = self.downloadFile(self.fishApi, savePath)
                if fishPath:
                    break
                continue
        return fishPath

    def getKfc(self, ):
        """
        疯狂星期四
        :return:
        """
        op(f'[*]: 正在调用KFC疯狂星期四Api接口... ... ')
        try:
            jsonData = requests.get(url=self.kfcApi, timeout=30).json()
            result = jsonData.get('text')
            if result:
                return result
            return None
        except Exception as e:
            op(f'[-]: KFC疯狂星期四Api接口出现错误, 错误信息: {e}')
            return None

    def getDog(self, ):
        """
        舔狗日记Api接口
        :return:
        """
        op(f'[*]: 正在调用舔狗日记Api接口... ... ')
        try:
            jsonData = requests.get(url=self.dogApi.format(self.txKey), timeout=30).json()
            result = jsonData.get('result')
            if result:
                content = result.get('content')
                if content:
                    return content
            return None
        except Exception as e:
            op(f'[-]: 舔狗日记Api接口出现错误, 错误信息: {e}')
            return None


if __name__ == '__main__':
    Ha = HappyApi()
    # print(Ha.getDog())
    print(Ha.getKfc())
