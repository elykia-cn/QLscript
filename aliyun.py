import json
import os
import requests
import urllib3
import notify  # 引入青龙面板的通知模块

urllib3.disable_warnings()

class AliYun:
    """阿里云盘签到器"""
    name = "阿里云盘"

    def __init__(self):
        """初始化，获取环境变量中的 token"""
        self.refresh_token = os.getenv("ALIYUNDRIVE_TOKEN")
        if not self.refresh_token:
            raise ValueError("请设置ALIYUNDRIVE_TOKEN环境变量")

    def update_token(self, refresh_token):
        """更新token"""
        url = "https://auth.aliyundrive.com/v2/account/token"
        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
        response = requests.post(url=url, json=data).json()
        access_token = response.get("access_token")
        return access_token

    def sign(self, access_token):
        """执行签到操作"""
        url = "https://member.aliyundrive.com/v1/activity/sign_in_list"
        headers = {"Authorization": access_token, "Content-Type": "application/json"}
        result = requests.post(url=url, headers=headers, json={}).json()
        sign_days = result["result"]["signInCount"]
        data = {"signInDay": sign_days}
        url_reward = "https://member.aliyundrive.com/v1/activity/sign_in_reward"
        requests.post(url=url_reward, headers=headers, data=json.dumps(data))

        # 检查签到结果
        if "success" in result:
            logging_info = f"✅【签到成功】\n累计签到天数：{sign_days} 天"
            for i, j in enumerate(result["result"]["signInLogs"]):
                if j["status"] == "miss":
                    day_json = result["result"]["signInLogs"][i - 1]
                    if not day_json["isReward"]:
                        msg = [
                            {"name": "阿里云盘", "value": f"签到成功，今日未获得奖励"}
                        ]
                    else:
                        msg = [
                            {"name": "累计签到", "value": f"{sign_days} 天"},
                            {"name": "阿里云盘", "value": f"获得奖励：{day_json['reward']['name']} - {day_json['reward']['description']}"}
                        ]
                    self.send_notification(logging_info, msg)
                    return msg
        else:
            msg = [{"name": "阿里云盘", "value": "签到失败，可能是token过期或其他错误"}]
            self.send_notification("❌【签到失败】\n可能是token过期或其他原因。", msg)
            return msg

    def send_notification(self, result: str, msg: list):
        """发送详细签到结果通知"""
        try:
            # 包含值的结果一起发送通知
            notify.send(self.name, f"{result}\n" + "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg]))
            print("通知已发送:", result)  # 打印通知内容
        except Exception as e:
            print(f"通知发送失败: {str(e)}")

    def main(self):
        """主执行逻辑"""
        access_token = self.update_token(self.refresh_token)
        if not access_token:
            msg = [{"name": "阿里云盘", "value": "token过期"}]
            self.send_notification("❌【签到失败】\ntoken过期", msg)
            return msg

        msg = self.sign(access_token)
        msg_str = "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])
        return msg_str


if __name__ == "__main__":
    try:
        # 启动签到任务
        checker = AliYun()
        result = checker.main()
        print(result)
    except Exception as e:
        print(f"运行失败: {str(e)}")
