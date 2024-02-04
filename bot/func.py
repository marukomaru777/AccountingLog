from bot.models import User, Expenses, Category, ExpenseResult
from django.db.models import Sum
from datetime import datetime
import calendar
import json

from linebot.models import (
    TextSendMessage,
    QuickReply,
    QuickReplyButton,
    FlexSendMessage,
    PostbackAction,
)


def MsgEvent(user_id, msg):
    if User.objects.filter(user_id=user_id).exists():
        if "明細" in msg.upper():
            if "今日" in msg.upper() or "今天" in msg.upper():
                date_from = datetime.now().date()
                date_to = datetime.now().date()
            else:
                now = datetime.now()
                date_from = datetime(now.year, now.month, 1)
                date_to = datetime(
                    now.year, now.month, calendar.monthrange(now.year, now.month)[1]
                )
            msg_return = GetDetMsg(user_id, date_from, date_to)
        elif "統計" in msg.upper():
            now = datetime.now()
            date_from = datetime(now.year, now.month, 1)
            date_to = datetime(
                now.year, now.month, calendar.monthrange(now.year, now.month)[1]
            )
            msg_return = GetAggMsg(user_id, date_from, date_to)
        else:
            data = ChkInputMsg(msg)
            if data.result:
                c_list = GetCategory(user_id, data.type)
                items = []
                for i in c_list:
                    data.type = i["c_type"]
                    data.c_id = i["c_id"]
                    item = QuickReplyButton(
                        action=PostbackAction(
                            label=i["c_name"], data=json.dumps(data.__dict__)
                        )
                    )
                    items.append(item)
                msg_return = TextSendMessage(
                    text="請選擇消費分類", quick_reply=QuickReply(items)
                )
            else:
                msg_return = TextSendMessage(text="輸入格式錯誤！")
    else:
        if Register(user_id):
            msg_return = TextSendMessage(text="註冊成功！")
        else:
            msg_return = TextSendMessage(text="註冊失敗QAQ")
    return msg_return


def Register(user_id):
    try:
        User.objects.create(user_id=user_id)
        expense_list = ["飲食", "繳費", "日常", "購物", "娛樂", "其他"]
        income_list = ["薪水", "獎金", "兼職", "投資", "零用錢", "其他"]
        for i in income_list:
            Category.objects.create(user_id=user_id, c_type="+", c_name=i)
        for i in expense_list:
            Category.objects.create(user_id=user_id, c_type="-", c_name=i)
        return True
    except Exception:
        return False


def ChkInputMsg(msg):
    if msg[0] == "+":
        type = "+"
        msg = msg[1:]
    else:
        type = "-"
    input_list = msg.strip().split()
    if len(input_list) == 2:
        if IsFloat(input_list[0]):
            amount = int(input_list[0])
            desc = input_list[1]
        elif IsFloat(input_list[1]):
            amount = int(input_list[1])
            desc = input_list[0]
        # 需再判斷收入or支出
        return ExpenseResult(True, type, amount, desc)
    else:
        return ExpenseResult(False)


def IsFloat(str):
    s = str.split(".")
    if len(s) > 2:
        return False
    else:
        for si in s:
            if not si.isdigit():
                return False
        return True


def GetCategory(user_id, c_type):
    c_set = Category.objects.filter(user_id=user_id, c_type=c_type).values(
        "c_id", "c_type", "c_name"
    )
    if c_set.count() > 0:
        return list(c_set)
    else:
        raise Exception("No Category.")


def AddExpensesLog(model):
    Expenses.objects.create(
        user_id=model.user_id,
        c_id=model.c_id,
        e_date=model.e_date,
        e_type=model.e_type,
        e_amount=model.e_amount,
        e_desc=model.e_desc,
    )
    return True


def GetExpenseDetail(user_id, date_from, date_to):
    result = Expenses.objects.filter(
        user_id=user_id, e_date__range=[date_from, date_to]
    ).values()
    return list(result)


def GetExpenseAgg(user_id, e_type, date_from, date_to):
    result = (
        Expenses.objects.values("c_id")
        .filter(user_id=user_id, e_type=e_type, e_date__range=[date_from, date_to])
        .annotate(amount_sum=Sum("e_amount"))
    )
    return list(result)


def GetDetMsg(user_id, date_from, date_to):
    result = GetExpenseDetail(
        user_id, date_from.strftime("%Y-%m-%d"), date_to.strftime("%Y-%m-%d")
    )
    items = []
    total_amount = 0
    for i in result:
        total_amount += int(i["e_amount"])
        item = {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": i["e_date"].strftime("%Y/%m/%d"),
                    "size": "sm",
                    "color": "#555555",
                    "flex": 0,
                },
                {
                    "type": "text",
                    "text": Category.objects.get(c_id=i["c_id"]).c_name,
                    "size": "sm",
                    "color": "#555555",
                    "flex": 0,
                    "margin": "md",
                },
                {
                    "type": "text",
                    "text": "NT$ " + f"{i['e_amount']:,}",
                    "size": "sm",
                    "color": "#555555",
                    "flex": 0,
                    "margin": "md",
                    "align": "center",
                },
                {
                    "type": "text",
                    "text": i["e_desc"],
                    "size": "sm",
                    "color": "#555555",
                    "align": "start",
                    "margin": "md",
                },
            ],
        }
        items.append(item)

    msg_return = FlexSendMessage(
        alt_text="收支明細",
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "收支明細",
                        "weight": "bold",
                        "color": "#1DB446",
                        "size": "sm",
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "NT$ " + f"{total_amount:,}",
                                "size": "xxl",
                                "color": "#555555",
                                "flex": 0,
                                "weight": "bold",
                            },
                            {
                                "type": "text",
                                "size": "xxl",
                                "color": "#555555",
                                "align": "end",
                                "weight": "bold",
                                "text": "Total",
                            },
                        ],
                    },
                    {
                        "type": "text",
                        "size": "xs",
                        "color": "#aaaaaa",
                        "wrap": True,
                        "text": date_from.strftime("%Y/%m/%d")
                        + " ~ "
                        + date_to.strftime("%Y/%m/%d"),
                    },
                    {"type": "separator", "margin": "xxl"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "xxl",
                        "spacing": "sm",
                        "contents": items,
                    },
                ],
            },
            "styles": {"footer": {"separator": True}},
        },
    )
    return msg_return


def GetAggMsg(user_id, date_from, date_to):
    expense_result = GetExpenseAgg(user_id, "-", date_from, date_to)
    income_result = GetExpenseAgg(user_id, "+", date_from, date_to)
    total_expense = 0
    total_income = 0
    income_items = [
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": "收入",
                    "size": "sm",
                    "color": "#555555",
                    "flex": 0,
                }
            ],
        }
    ]
    for i in income_result:
        total_income += int(i["amount_sum"])
        item = {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": Category.objects.get(c_id=i["c_id"]).c_name,
                    "size": "sm",
                    "color": "#555555",
                    "flex": 0,
                },
                {
                    "type": "text",
                    "text": "NT$ " + f"{int(i['amount_sum']):,}",
                    "size": "sm",
                    "color": "#111111",
                    "align": "end",
                },
            ],
        }
        income_items.append(item)
    expense_items = [
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": "支出",
                    "size": "sm",
                    "color": "#555555",
                    "flex": 0,
                }
            ],
        }
    ]
    for i in expense_result:
        total_expense += int(i["amount_sum"])
        item = {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": Category.objects.get(c_id=i["c_id"]).c_name,
                    "size": "sm",
                    "color": "#555555",
                    "flex": 0,
                },
                {
                    "type": "text",
                    "text": "NT$ " + f"{int(i['amount_sum']):,}",
                    "size": "sm",
                    "color": "#111111",
                    "align": "end",
                },
            ],
        }
        expense_items.append(item)
    items = income_items + [{"type": "separator", "margin": "xxl"}] + expense_items
    msg_return = FlexSendMessage(
        alt_text="收支統計",
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "收支統計",
                        "weight": "bold",
                        "color": "#1DB446",
                        "size": "sm",
                    },
                    {
                        "type": "text",
                        "text": "收入",
                        "weight": "bold",
                        "size": "md",
                        "margin": "md",
                    },
                    {
                        "type": "text",
                        "text": "NT$ " + f"{total_income:,}",
                        "weight": "bold",
                        "size": "xxl",
                        "margin": "md",
                    },
                    {
                        "type": "text",
                        "text": "支出",
                        "weight": "bold",
                        "size": "md",
                        "margin": "md",
                    },
                    {
                        "type": "text",
                        "text": "NT$ " + f"{total_expense:,}",
                        "weight": "bold",
                        "size": "xxl",
                        "margin": "md",
                    },
                    {
                        "type": "text",
                        "text": date_from.strftime("%Y/%m/%d")
                        + " ~ "
                        + date_to.strftime("%Y/%m/%d"),
                        "size": "xs",
                        "color": "#aaaaaa",
                        "wrap": True,
                    },
                    {"type": "separator", "margin": "xxl"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "xxl",
                        "spacing": "sm",
                        "contents": items,
                    },
                    {"type": "separator", "margin": "xxl"},
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "收支",
                                "size": "xs",
                                "color": "#aaaaaa",
                                "flex": 0,
                            },
                            {
                                "type": "text",
                                "text": "NT$ " + f"{total_income-total_expense:,}",
                                "color": "#aaaaaa",
                                "size": "xs",
                                "align": "end",
                            },
                        ],
                    },
                ],
            },
            "styles": {"footer": {"separator": True}},
        },
    )
    return msg_return


def PstBkEvent(user_id, postback_str):
    postback_data = json.loads(postback_str)
    model = Expenses(
        user_id=user_id,
        c_id=postback_data["c_id"],
        e_type=postback_data["type"],
        e_amount=postback_data["e_amount"],
        e_desc=postback_data["e_desc"],
        e_date=datetime.now().strftime("%Y-%m-%d"),
    )
    if AddExpensesLog(model):
        c_name = Category.objects.get(c_id=model.c_id).c_name
        msg_return = FlexSendMessage(
            alt_text="新增結果",  # 聊天列表所顯示的訊息
            contents={
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "新增成功",
                            "weight": "bold",
                            "color": "#1DB446",
                            "size": "sm",
                        },
                        {
                            "type": "text",
                            "text": "NT$ " + f"{model.e_amount:,}",
                            "weight": "bold",
                            "size": "xxl",
                            "margin": "md",
                        },
                        {
                            "type": "text",
                            "size": "xs",
                            "color": "#aaaaaa",
                            "wrap": True,
                            "text": c_name,
                        },
                        {"type": "separator", "margin": "xxl"},
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "xxl",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "日期",
                                            "size": "sm",
                                            "color": "#555555",
                                            "flex": 0,
                                        },
                                        {
                                            "type": "text",
                                            "text": model.e_date,
                                            "size": "sm",
                                            "color": "#111111",
                                            "align": "end",
                                        },
                                    ],
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "size": "sm",
                                            "color": "#555555",
                                            "flex": 0,
                                            "text": "備註",
                                        },
                                        {
                                            "type": "text",
                                            "text": model.e_desc,
                                            "size": "sm",
                                            "color": "#111111",
                                            "align": "end",
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
                "styles": {"footer": {"separator": True}},
            },
        )
    else:
        msg_return = TextSendMessage(text="新增失敗")
    return msg_return


def UnfolwEvent(user_id):
    if Expenses.objects.filter(user_id=user_id).exists():
        Expenses.objects.filter(user_id=user_id).delete()

    if Category.objects.filter(user_id=user_id).exists():
        Category.objects.filter(user_id=user_id).delete()

    if User.objects.filter(user_id=user_id).exists():
        User.objects.filter(user_id=user_id).delete()
