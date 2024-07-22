import os
import re
from time import sleep
import Config.ConfigServer as Cs

from DbServer.DbMainServer import DbMainServer
from BotServer.BotFunction.InterfaceFunction import *
from PIL import Image
import imagehash
import cv2
from pyzbar.pyzbar import decode
import FileCache.FileCacheServer as Fcs


def check_img_tag(text):
    pattern = re.compile(r'<img.*?>', re.DOTALL)
    return bool(pattern.search(text))


def get_images_from_all(folder_path):
    abs_folder_path = os.path.abspath(folder_path)
    images = []
    for file_name in os.listdir(abs_folder_path):
        if file_name.endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif')):
            img_path = os.path.join(abs_folder_path, file_name)
            images.append(img_path)
    return images


def is_same_image(image1_path, image2_path):
    # 打开图像
    image1 = Image.open(image1_path)
    image2 = Image.open(image2_path)

    # 计算图像的哈希值
    hash1 = imagehash.phash(image1)
    hash2 = imagehash.phash(image2)

    # 比较哈希值，允许一定的误差
    return hash1 - hash2 == 0


class CodeFunction:

    def __init__(self, wcf):
        self.wcf = wcf
        self.Dms = DbMainServer()
        configData = Cs.returnConfigData()
        self.addAdminKeyWords = configData['adminFunctionWord']['addAdminWord']
        self.delAdminKeyWords = configData['adminFunctionWord']['delAdminWord']
        self.zhuanfa_qun_ids = configData['zhuanfaqun']
        self.zhuanfaqun_deng_ids = configData['zhuanfaqun_deng']
        self.all_mas_qun = configData['all_mas_qun']

    def save_image_for_qun(self, msg):

        if check_img_tag(msg.content.strip()):
            sleep(1)
            folder_path = Fcs.returnAllImageQunCacheFolder() + '/'
            imageList = get_images_from_all(folder_path)
            save_path = self.save_all_image(msg)
            if save_path == "":
                self.wcf.send_text(msg=" 下载图片失败！！！！", receiver="wxid_hzicw1nyk8dy22")
                return
            code = self.qrcode_recongnize(save_path)
            room_name = getIdName(self.wcf, msg.roomid)
            if code == 0:
                if os.path.exists(save_path):
                    self.wcf.send_image(path=save_path, receiver="48265783292@chatroom")
                    self.wcf.send_text(msg=f'群聊：{room_name}\n 不包含二维码  文件已删除！！',
                                       receiver="48265783292@chatroom")
                    os.remove(save_path)
                    return
                else:
                    op("文件不存在！！")
                    return
            for image in imageList:
                isHave = is_same_image(save_path, image)
                if isHave:
                    os.remove(save_path)
                    op("图片已存在  文件已删除！！")
                    return

    def forward_all_qun(self, msg):
        save_path = self.save_wei_image(msg)
        isTure = True
        if save_path == "":
            self.wcf.send_text(msg=" 下载图片失败！！！！", receiver="love623954275")
            return
        all_mas_qun = self.all_mas_qun
        for administrator in all_mas_qun:
            if self.wcf.send_file(path=save_path, receiver=administrator) != 0:
                isTure = False
        if isTure:
            self.wcf.send_text(msg=" 转发成功 ", receiver="48141784335@chatroom")
        else:
            self.wcf.send_text(msg=" 转发失败！！！ ", receiver="48141784335@chatroom")

    def qrcode_recongnize(self, save_path):
        haveQrCode = 0
        try:
            # 读取图片
            image = cv2.imread(save_path)
            # 灰度化
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # 解码二维码
            result = decode(image)
            if len(result) > 0:
                haveQrCode = 1
        except Exception as e:
            msg = f' 整合图片出现错误, 错误信息：{e}'
            op(msg)
            haveQrCode = self.qrcode_recongnize(save_path)
        return haveQrCode

    def save_wei_image(self, msg):
        sleep(1)
        savePath = Fcs.returnPicCacheFolder() + '/'
        max_num = 10
        retries = 0
        save_path_new = ""
        while retries < max_num:
            save_path_new = self.wcf.download_image(msg.id, msg.extra, savePath)
            if save_path_new != "":  # 如果返回非空字符串，跳出循环
                break
            retries += 1
        if save_path_new == "":  # 如果达到最大重试次数仍然失败，可以处理错误
            print("已达最大下载次数。。。。")
        return save_path_new

    def save_all_image(self, msg):
        sleep(1)
        savePath = Fcs.returnPicCacheFolder() + '/'
        max_num = 10
        retries = 0
        save_path_new = ""
        while retries < max_num:
            save_path_new = self.wcf.download_image(msg.id, msg.extra, savePath)
            if save_path_new != "":  # 如果返回非空字符串，跳出循环
                break
            retries += 1
        if save_path_new == "":  # 如果达到最大重试次数仍然失败，可以处理错误
            print("已达最大下载次数。。。。")
        return save_path_new

    def forward_cesimsg(self, msg):

        save_path = self.save_wei_image(msg)
        isTure = True
        if save_path == "":
            self.wcf.send_text(msg=" 下载图片失败！！！！", receiver="wxid_hzicw1nyk8dy22")
            return
        room_dicts = self.zhuanfa_qun_ids
        for administrator in room_dicts:
            if self.wcf.send_file(path=save_path, receiver=administrator) != 0:
                isTure = False
        if isTure:
            self.wcf.send_text(msg=" 转发成功 ", receiver="wxid_hzicw1nyk8dy22")
        else:
            self.wcf.send_text(msg=" 转发失败！！！ ", receiver="wxid_hzicw1nyk8dy22")

    def forward_cesimsg_deng(self, msg):

        save_path = self.save_wei_image(msg)
        isTure = True
        if save_path == "":
            self.wcf.send_text(msg=" 下载图片失败！！！！", receiver="wxid_9oqjxmagzl8122")
            return
        room_dicts = self.zhuanfaqun_deng_ids
        for administrator in room_dicts:
            if self.wcf.send_file(path=save_path, receiver=administrator) != 0:
                isTure = False
        if isTure:
            self.wcf.send_text(msg=" 转发成功 ", receiver="wxid_9oqjxmagzl8122")
        else:
            self.wcf.send_text(msg=" 转发失败！！！ ", receiver="wxid_9oqjxmagzl8122")

    def forward_qunmsg(self, msg):
        save_path = self.save_wei_image(msg)
        isTure = True
        if save_path == "":
            self.wcf.send_text(msg=" 下载图片失败！！！！", receiver="love623954275")
            return
        room_dicts = self.Dms.showPushRoom()
        for administrator in room_dicts:
            if self.wcf.send_file(path=save_path, receiver=administrator) != 0:
                isTure = False
        if isTure:
            self.wcf.send_text(msg=" 转发成功 ", receiver="love623954275")
        else:
            self.wcf.send_text(msg=" 转发失败！！！ ", receiver="love623954275")
        # if status == 0:
        #     self.wcf.send_text(f'图片转发自：{self.wcf.get_info_by_wxid(msg.sender).get("name")}', administrator)
