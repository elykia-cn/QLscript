import json
import os
import re
import requests
import urllib3
import notify  # 引入青龙面板的通知模块


urllib3.disable_warnings()


class EnShan(CheckIn):
    name = "恩山无线论坛"

    def __init__(self, check_item):
        self.check_item = check_item

    @staticmethod
    def sign():
        # 从环境变量获取 ENSHAN_COOKIE
        cookie = os.getenv("ENSHAN_COOKIE")
        if not cookie:
            raise ValueError("请设置 ENSHAN_COOKIE 环境变量")

        msg = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36",
            "Cookie": cookie,
        }
        response = requests.get(
            url="https://www.right.com.cn/FORUM/home.php?mod=spacecp&ac=credit&showcredit=1",
            headers=headers,
            verify=False,
        )
        try:
            # 使用正则表达式提取“恩山币”
            coin = re.findall("恩山币: </em>(.*?)&nbsp;", response.text)
            point = re.findall("<em>积分: </em>(.*?)<span", response.text)
            
            if coin and point:  # 如果两个值都成功提取
                msg = [
                    {"name": "恩山币", "value": coin[0]},
                    {"name": "积分", "value": point[0]},
                ]
                # 发送通知
                notification_msg = f"✅【签到成功】\n恩山币: {coin[0]}\n积分: {point[0]}"
                EnShan.send_notification(notification_msg)
            else:
                raise ValueError("无法提取到恩山币或积分，可能页面结构已变更。")
        except Exception as e:
            msg = [{"name": "签到失败", "value": f"错误: {str(e)}"}]
            # 发送签到失败的通知
            notification_msg = f"❌【签到失败】\n错误: {str(e)}"
            EnShan.send_notification(notification_msg)

        return msg

    @staticmethod
    def send_notification(result: str):
        """发送签到结果的通知到青龙面板"""
        try:
            # 发送通知到青龙面板
            notify.send("恩山无线论坛", result)
            print(f"通知已发送: {result}")
        except Exception as e:
            print(f"通知发送失败: {str(e)}")

    def main(self):
        msg = self.sign()
        msg = "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])
        return msg


if __name__ == "__main__":
    try:
        print(EnShan(check_item={}).main())
    except ValueError as e:
        print(str(e))
