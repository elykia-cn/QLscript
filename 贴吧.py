import os
import requests
import hashlib
import re
import time
import random
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import notify  # 青龙面板的通知模块

class Tieba:
    """百度贴吧签到器"""
    name = "百度贴吧"

    def __init__(self):
        """初始化，获取cookie"""
        self.tieba_cookie = os.getenv("TIEBA_COOKIE")
        if not self.tieba_cookie:
            raise ValueError("请设置TIEBA_COOKIE环境变量")

    @staticmethod
    def login_info(session):
        """获取登录信息"""
        return session.get(url="https://zhidao.baidu.com/api/loginInfo").json()

    def valid(self, session):
        """验证登录状态"""
        try:
            content = session.get(url="https://tieba.baidu.com/dc/common/tbs")
        except Exception as e:
            return False, f"登录验证异常,错误信息: {e}"

        data = content.json()
        if data["is_login"] == 0:
            return False, "登录失败,cookie 异常"

        tbs = data["tbs"]
        user_name = self.login_info(session=session)["userName"]
        return tbs, user_name

    @staticmethod
    def tieba_list_more(session):
        """获取贴吧列表"""
        content = session.get(
            url="https://tieba.baidu.com/f/like/mylike?&pn=1",
            timeout=(5, 20),
            allow_redirects=False,
        )
        try:
            pn = int(
                re.match(
                    r".*/f/like/mylike\?&pn=(.*?)\">尾页.*", content.text, re.S | re.I
                ).group(1)
            )
        except Exception:
            pn = 1

        next_page = 1
        pattern = re.compile(r".*?<a href=\"/f\?kw=.*?title=\"(.*?)\">")
        while next_page <= pn:
            tbname = pattern.findall(content.text)
            yield from tbname
            next_page += 1
            content = session.get(
                url=f"https://tieba.baidu.com/f/like/mylike?&pn={next_page}",
                timeout=(5, 20),
                allow_redirects=False,
            )

    def get_tieba_list(self, session):
        """获取所有贴吧名称"""
        tieba_list = list(self.tieba_list_more(session=session))
        return tieba_list

    @staticmethod
    def sign(session, tb_name_list, tbs):
        """执行签到操作"""
        success_count, error_count, exist_count, shield_count = 0, 0, 0, 0
        
        def sign_one_bar(tb_name):
            """签到单个贴吧"""
            md5 = hashlib.md5(f"kw={tb_name}tbs={tbs}tiebaclient!!!".encode()).hexdigest()
            data = {"kw": tb_name, "tbs": tbs, "sign": md5}
            try:
                response = session.post(
                    url="https://c.tieba.baidu.com/c/c/forum/sign",
                    data=data,
                    verify=False,
                ).json()
                if response["error_code"] == "0":
                    return {"tb_name": tb_name, "status": "签到成功"}
                elif response["error_code"] == "160002":
                    return {"tb_name": tb_name, "status": "已经签到"}
                elif response["error_code"] == "340006":
                    return {"tb_name": tb_name, "status": "被屏蔽"}
                else:
                    return {"tb_name": tb_name, "status": "签到失败"}
            except Exception as e:
                return {"tb_name": tb_name, "status": f"签到异常: {e}"}

        # 使用线程池进行并发签到
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(sign_one_bar, tb_name) for tb_name in tb_name_list]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # 统计签到结果
        for result in results:
            if result["status"] == "签到成功":
                success_count += 1
            elif result["status"] == "已经签到":
                exist_count += 1
            elif result["status"] == "被屏蔽":
                shield_count += 1
            else:
                error_count += 1

        # 格式化签到结果
        msg = [
            {"name": "贴吧总数", "value": len(tb_name_list)},
            {"name": "签到成功", "value": success_count},
            {"name": "已经签到", "value": exist_count},
            {"name": "被屏蔽的", "value": shield_count},
            {"name": "签到失败", "value": error_count},
        ]
        return msg

    def send_notification(self, result: str):
        """发送签到结果通知"""
        try:
            notify.send(self.name, result)
            print("通知已发送:", result)  # 打印通知内容
        except Exception as e:
            print(f"通知发送失败: {str(e)}")

    def main(self):
        """主执行逻辑"""
        tieba_cookie = {
            item.split("=")[0]: item.split("=")[1]
            for item in self.tieba_cookie.split("; ")
        }
        session = requests.session()
        requests.utils.add_dict_to_cookiejar(session.cookies, tieba_cookie)
        session.headers.update({"Referer": "https://www.baidu.com/"})

        # 验证登录状态
        tbs, user_name = self.valid(session=session)
        if tbs:
            # 获取贴吧列表并执行签到
            tb_name_list = self.get_tieba_list(session=session)
            msg = self.sign(session=session, tb_name_list=tb_name_list, tbs=tbs)
            msg = [{"name": "帐号信息", "value": user_name}] + msg
            self.send_notification(f"✅【签到成功】\n{user_name} 贴吧签到完成")
        else:
            msg = [
                {"name": "帐号信息", "value": user_name},
                {"name": "签到信息", "value": "Cookie 可能过期"},
            ]
            self.send_notification(f"❌【签到失败】\n{user_name} 登录失败，请检查Cookie。")
        
        # 格式化并返回消息
        msg_str = "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])
        return msg_str


if __name__ == "__main__":
    try:
        # 启动签到任务
        tieba = Tieba()
        result = tieba.main()
        print(result)
    except Exception as e:
        print(f"运行失败: {str(e)}")
