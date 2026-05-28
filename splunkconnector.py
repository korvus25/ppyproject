import splunklib.client as client
service = client.connect(
url = "https://prd-p-dlzxv.splunkcloud.com",
    username = "********",
    password = "************",
)
for app in service.apps:
    print(app.name)