import requests, json, time, os, sys
from lxml import etree

sys.path.append('.')
requests.packages.urllib3.disable_warnings()

# 通知发送函数
def send_notification_message(title: str, message: str):
    try:
        # 模拟发送通知的功能（可以根据实际情况修改）
        # 比如用 Server 酱等方式发送
        print(f"通知 - {title}: {message}")
    except Exception as e:
        print(f"通知发送失败: {e}")

def run(cookie: str) -> str:
    msg = ""
    s = requests.Session()
    s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'})

    # 签到
    url = "https://www.right.com.cn/forum/home.php?mod=spacecp&ac=credit&op=log&suboperation=creditrulelog"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0',
        'Connection' : 'keep-alive',
        'Host' : 'www.right.com.cn',
        'Upgrade-Insecure-Requests' : '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language' : 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding' : 'gzip, deflate, br',
        'Cookie': cookie
    }
    
    try:
        r = s.get(url, headers=headers, timeout=120)
        if '每天登录' in r.text:
            h = etree.HTML(r.text)
            data = h.xpath('//tr/td[6]/text()')
            msg += f'签到成功或今日已签到，最后签到时间：{data[0]}'
        else:
            msg += '签到失败，可能是cookie失效了！'
            send_notification_message("恩山论坛签到失败", msg)  # 发送签到失败通知
    except requests.exceptions.RequestException as e:
        msg = f'请求失败: {str(e)}'
        send_notification_message("恩山论坛签到失败", msg)
    except Exception as e:
        msg = '无法正常连接到网站，请尝试改变网络环境，试下本地能不能跑脚本，或者换几个时间点执行脚本'
        send_notification_message("恩山论坛签到异常", msg)

    return msg + '\n'

def main(cookie: str):
    msg = ""
    clist = cookie.split("\n") if "\\n" not in cookie else cookie.split("\\n")
    i = 0
    while i < len(clist):
        msg += f"第 {i+1} 个账号开始执行任务\n"
        current_cookie = clist[i]
        msg += run(current_cookie)
        i += 1
    
    print(msg[:-1])  # 打印最后的结果
    send_notification_message("恩山论坛签到结束", "所有账号签到完成！")  # 发送签到完成通知
    return msg[:-1]

if __name__ == "__main__":
    cookie = os.environ.get("cookie_enshan")  # 获取环境变量cookie

    if cookie:
        print("----------恩山论坛开始尝试签到----------")
        result = main(cookie)  # 调用签到主函数
        print("----------恩山论坛签到执行完毕----------")
        send_notification_message("恩山论坛签到结果", result)  # 发送签到结果通知
    else:
        print("未找到cookie，请设置cookie_enshan环境变量")
        send_notification_message("恩山论坛签到失败", "未找到cookie_enshan环境变量")
