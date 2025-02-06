import os
import re
import logging
from typing import List, Dict
import requests
import urllib3
from dailycheckin import CheckIn
import notify  # 引入青龙面板的通知模块

# 禁用SSL警告
urllib3.disable_warnings()

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

class EnShan(CheckIn):
    """恩山无线论坛签到器"""
    name = "恩山无线论坛"
    
    # 常量定义
    CREDIT_URL = "https://www.right.com.cn/FORUM/home.php?mod=spacecp&ac=credit&showcredit=1"
    USER_AGENT = os.getenv("ENSHAN_UA", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    COIN_PATTERN = r"恩山币: </em>(.*?)&nbsp;"
    POINT_PATTERN = r"<em>积分: </em>(.*?)<span"

    def __init__(self, check_item: Dict = None):
        super().__init__()  # 调用父类的无参数构造方法
        self.cookie = self._get_cookie()

    def _get_cookie(self) -> str:
        """从环境变量获取Cookie"""
        cookie = os.getenv("ENSHAN_COOKIE")
        if not cookie:
            raise ValueError("未找到ENSHAN_COOKIE环境变量配置")
        return cookie

    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        return {
            "User-Agent": self.USER_AGENT,
            "Cookie": self.cookie,
            "Referer": self.CREDIT_URL
        }

    def _parse_credit(self, response_text: str) -> List[Dict[str, str]]:
        """解析积分信息"""
        try:
            coin = re.findall(self.COIN_PATTERN, response_text)[0]
            point = re.findall(self.POINT_PATTERN, response_text)[0]
            return [
                {"name": "恩山币", "value": coin},
                {"name": "积分", "value": point}
            ]
        except IndexError as e:
            logging.error("解析页面数据失败，可能页面结构已变更")
            raise RuntimeError("解析积分信息失败") from e

    def sign(self) -> List[Dict[str, str]]:
        """执行签到操作"""
        try:
            response = requests.get(
                url=self.CREDIT_URL,
                headers=self._build_headers(),
                verify=False,
                timeout=10
            )
            response.raise_for_status()

            # 判断签到是否成功
            if '每天登录' in response.text:
                h = etree.HTML(response.text)
                data = h.xpath('//tr/td[6]/text()')
                msg = f"签到成功或今日已签到，最后签到时间：{data[0]}"
                logging.info(msg)
                self.send_notification(msg)  # 发送签到成功通知
            else:
                msg = '签到失败，可能是cookie失效了！'
                logging.error(msg)
                self.send_notification(msg)  # 发送签到失败通知

            return self._parse_credit(response.text)
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {str(e)}")
            msg = "签到失败，网络请求异常"
            self.send_notification(msg)  # 发送网络请求失败通知
            return [{"name": "签到失败", "value": msg}]
        except Exception as e:
            logging.error(f"未知错误: {str(e)}")
            msg = "签到失败，系统异常"
            self.send_notification(msg)  # 发送系统错误通知
            return [{"name": "签到失败", "value": msg}]

    def send_notification(self, result: str) -> None:
        """发送签到结果通知"""
        try:
            # 使用青龙面板的通知功能发送通知
            notify.send("恩山无线论坛签到结果", result)
        except Exception as e:
            logging.error(f"通知发送失败: {str(e)}")

    def main(self) -> str:
        """主执行逻辑"""
        result = self.sign()
        result_text = "\n".join([f"{item['name']}: {item['value']}" for item in result])
        return result_text

if __name__ == "__main__":
    # 从环境变量读取配置
    cookie = os.getenv("ENSHAN_COOKIE")
    
    if not cookie:
        logging.error("请设置ENSHAN_COOKIE环境变量")
        exit(1)
        
    checker = EnShan(check_item={"cookie": cookie})
    print(checker.main())
