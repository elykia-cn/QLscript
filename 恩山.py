import os
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
        """初始化，获取cookie"""
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
            logging.info("开始进行签到请求...")
            with requests.Session() as s:
                s.headers.update(self._build_headers())
                response = s.get(self.CREDIT_URL, timeout=10)
                response.raise_for_status()

                # 判断签到是否成功（基于页面内容）
                if '每天登录' in response.text:
                    # 使用XPath提取最后签到时间（如果能提取）
                    h = etree.HTML(response.text)
                    last_sign_time = h.xpath('//td[@class="num"]/text()')[0] if h.xpath('//td[@class="num"]/text()') else None
                    
                    if last_sign_time:
                        msg = f"✅【签到成功】\n今日已成功签到！\n最后签到时间：{last_sign_time}"
                    else:
                        msg = '✅【签到成功】\n今日已成功签到！\n未能提取签到时间，可能页面结构已变更。'
                    
                    self.send_notification(msg)
                else:
                    msg = '❌【签到失败】\n签到失败，可能是cookie失效或签到状态异常！'
                    self.send_notification(msg)

        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {str(e)}")
            self.send_notification(f"❌【签到失败】\n网络请求失败：{str(e)}")
        except Exception as e:
            logging.error(f"未知错误: {str(e)}")
            self.send_notification(f"❌【签到失败】\n系统异常：{str(e)}")

    def send_notification(self, result: str):
        """发送详细签到结果通知"""
        try:
            # 发送通知到青龙面板
            notify.send("恩山无线论坛", result)
            logging.info("通知已发送: " + result)
        except Exception as e:
            logging.error(f"通知发送失败: {str(e)}")

    def main(self):
        """主执行逻辑"""
        self.sign()

if __name__ == "__main__":
    try:
        # 启动签到任务
        checker = EnShan()
        checker.main()
    except ValueError as e:
        logging.error(str(e))
