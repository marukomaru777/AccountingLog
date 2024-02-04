from django.shortcuts import render


# Create your views here.
def index(request):
    result = [
        {
            "date": "2024/01/01",
            "sum": 200,
            "detail": [
                {"class": "飲食", "tag": "晚餐", "amount": 75, "desc": "滷味"},
                {"class": "飲食", "tag": "飲料", "amount": 80, "desc": "迷客夏"},
            ],
        }
    ]
    return render(request, "index.html", {"result": result})
