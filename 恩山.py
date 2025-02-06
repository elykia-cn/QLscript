import os
import re
import logging
import requests
from lxml import etree
import notify  # 引入青龙面板的通知模块

# 配置日志记录
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class EnShan:
    """恩山无线论坛签到器"""
    CREDIT_URL = "https://www.right.com.cn/FORUM/home.php?mod=spacecp&ac=credit&showcredit=1"
    USER_AGENT = os.getenv("ENSHAN_UA", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    def __init__(self):
        self.cookie = os.getenv("ENSHAN_COOKIE")
        if not self.cookie:
            raise ValueError("请设置ENSHAN_COOKIE环境变量")

    def _build_headers(self):
        """构建请求头"""
        return {
            "User-Agent": self.USER_AGENT,
            "Cookie": self.cookie,
            "Referer": self.CREDIT_URL
        }

    def sign(self):
        """执行签到操作"""
        try:
            response = requests.get(self.CREDIT_URL, headers=self._build_headers(), timeout=10)
            response.raise_for_status()

            # 判断签到是否成功
            if '每天登录' in response.text:
                h = etree.HTML(response.text)
                data = h.xpath('//tr/td[6]/text()')
                msg = f"签到成功或今日已签到，最后签到时间：{data[0]}"
                self.send_notification(msg)
            else:
                msg = '签到失败，可能是cookie失效了！'
                self.send_notification(msg)

        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {str(e)}")
            self.send_notification("签到失败，网络请求异常")
        except Exception as e:
            logging.error(f"未知错误: {str(e)}")
            self.send_notification("签到失败，系统异常")

    def send_notification(self, result: str):
        """发送签到结果通知"""
        try:
            notify.send("恩山无线论坛签到结果", result)
        except Exception as e:
            logging.error(f"通知发送失败: {str(e)}")

    def main(self):
        """主执行逻辑"""
        self.sign()

if __name__ == "__main__":
    try:
        checker = EnShan()
        checker.main()
    except ValueError as e:
        logging.error(str(e))
