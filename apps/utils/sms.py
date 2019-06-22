import json
from Qcloud.Sms.sms import SmsSingleSender


def sms(phone, code):
    # 请根据实际 appid 和 appkey 进行开发，以下只作为演示 sdk 使用
    # appid,appkey,templId申请方式可参考接入指南https://www.qcloud.com/document/product/382/3785
    appid = 10000000
    appkey = ""

    single_sender = SmsSingleSender(appid, appkey)

    result = single_sender.send(0, "86", phone,
                                "您的登录验证码为{}，请于10分钟内填写。如非本人操作，请忽略本短信。".format(code), "", "", )
    result = json.loads(result)
    return result


if __name__ == '__main__':
    sms('18600335842', '1234')
