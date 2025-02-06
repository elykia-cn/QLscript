import os
import re
import logging
import requests
import urllib3
from typing import List, Dict, Union
from dailycheckin import CheckIn

# 禁用SSL警告
urllib3.disable_warnings()

# 配置日志记录
logging.basicConfig(
    level=logging.DEBUG,  # 设置为DEBUG级别以捕获更多日志
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
        super().__init__(check_item)
        self.cookie = self._get_cookie()

    def _get_cookie(self) -> str:
        """从环境变量获取Cookie"""
        cookie = os.getenv("ENSHAN_COOKIE")
        if not cookie:
            raise ValueError("未找到ENSHAN_COOKIE环境变量配置")
        logging.debug(f"获取到的Cookie: {cookie}")  # 调试日志
        return cookie

    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "User-Agent": self.USER_AGENT,
            "Cookie": self.cookie,
            "Referer": self.CREDIT_URL
        }
        logging.debug(f"构建的请求头: {headers}")  # 调试日志
        return headers

    def _parse_credit(self, response_text: str) -> List[Dict[str, str]]:
        """解析积分信息"""
        try:
            logging.debug("开始解析积分信息")  # 调试日志
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
            logging.info("开始执行签到操作")  # 调试日志
            response = requests.get(
                url=self.CREDIT_URL,
                headers=self._build_headers(),
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            result = self._parse_credit(response.text)
            
            # 发送签到成功通知
            logging.info("签到成功，发送通知")  # 调试日志
            notify.sendNotify(title="恩山无线论坛签到成功", content=f"恩山币: {result[0]['value']}\n积分: {result[1]['value']}")
            
            return result
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {str(e)}")
            error_msg = "签到失败，网络请求异常"
            notify.sendNotify(title="恩山无线论坛签到失败", content=error_msg)
            return [{"name": "签到失败", "value": error_msg}]
        except Exception as e:
            logging.error(f"未知错误: {str(e)}")
            error_msg = "签到失败，系统异常"
            notify.sendNotify(title="恩山无线论坛签到失败", content=error_msg)
            return [{"name": "签到失败", "value": error_msg}]
