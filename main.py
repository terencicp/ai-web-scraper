from app.AppManager import AppManager

app = AppManager()
user_query = app.show_welcome_message()
user_intent, user_url, search_query = app.rewrite(user_query)
if user_url:
    urls = [user_url]
else:
    urls = app.search(search_query)
app.open_browser()
for i, url in enumerate(urls):
    data_valid, skip_url = False, False
    skip_url = app.browse(url, i)
    while not (data_valid or skip_url):
        data, skip_url = app.extract_data(user_intent)
        app.open_json_file()
        data_valid, skip_url = app.user_validates(data, skip_url)
    if data_valid:
        break
app.display_source_info()
