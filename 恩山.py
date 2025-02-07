import os
import re
import requests
import urllib3
import notify  # 引入青龙面板的通知模块

urllib3.disable_warnings()


class EnShan:
    name = "恩山无线论坛"

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
        try:
            response = requests.get(
                url="https://www.right.com.cn/FORUM/home.php?mod=spacecp&ac=credit&showcredit=1",
                headers=headers,
                verify=False,
            )
            response.raise_for_status()  # 检查请求是否成功

            # 使用正则表达式提取“恩山币”和“积分”
            coin = re.findall("恩山币: </em>(.*?)&nbsp;", response.text)
            point = re.findall("<em>积分: </em>(.*?)<span", response.text)
            
            if coin and point:  # 如果两个值都成功提取
                msg = [
                    {"name": "恩山币", "value": coin[0]},
                    {"name": "积分", "value": point[0]},
                ]
                # 构造通知消息
                notification_msg = f"✅【签到成功】\n积分变更: 恩山币 +1\n恩山币: {coin[0]}\n积分: {point[0]}"
                EnShan.send_notification(notification_msg)
                
                # 输出详细日志
                print(f"签到成功！恩山币: {coin[0]}, 积分: {point[0]}")
            else:
                raise ValueError("无法提取到恩山币或积分，可能页面结构已变更。")
        except requests.exceptions.RequestException as e:
            # 请求失败时处理
            msg = [{"name": "签到失败", "value": f"请求错误: {str(e)}"}]
            notification_msg = f"❌【签到失败】\n请求错误: {str(e)}"
            EnShan.send_notification(notification_msg)
            print(f"请求失败: {str(e)}")
        except Exception as e:
            # 其他异常处理
            msg = [{"name": "签到失败", "value": f"错误: {str(e)}"}]
            notification_msg = f"❌【签到失败】\n错误: {str(e)}"
            EnShan.send_notification(notification_msg)
            print(f"签到失败: {str(e)}")

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


if __name__ == "__main__":
    try:
        print(EnShan.sign())
    except ValueError as e:
        print(str(e))
