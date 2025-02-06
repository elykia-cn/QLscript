import os
import re
import logging
from typing import List, Dict, Union
import requests
import urllib3
from dailycheckin import CheckIn

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
            return self._parse_credit(response.text)
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {str(e)}")
            return [{"name": "签到失败", "value": "网络请求异常"}]
        except Exception as e:
            logging.error(f"未知错误: {str(e)}")
            return [{"name": "签到失败", "value": "系统异常"}]

    def main(self) -> str:
        """主执行逻辑"""
        result = self.sign()
        return "\n".join([f"{item['name']}: {item['value']}" for item in result])

if __name__ == "__main__":
    # 从环境变量读取配置
    cookie = os.getenv("ENSHAN_COOKIE")
    
    if not cookie:
        logging.error("请设置ENSHAN_COOKIE环境变量")
        exit(1)
        
    checker = EnShan(check_item={"cookie": cookie})
    print(checker.main())
