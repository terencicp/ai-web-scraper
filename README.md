## Miney: Semi-autonomous list scraper

Hi! My name is Terenci Claramunt, and I'm a senior Data Science student.
I wrote this Python app to explore the current capabilities of LLMs as autonomous web scrapers.

The user can interact with Miney using the terminal, and the app is designed to extract lists of objects.
To use it, download the code, then execute `python3 main.py` and write a query such as:
- "Fortune 500 companies"
- "Penguin species"
- ...

The app will search relevant websites, find the data you're looking for and extract it in JSON format.
Then it will show you the resulting data and you can provide feedback to improve it.

Let's see Miney in action:

https://github.com/user-attachments/assets/6e770252-2c27-4345-bc64-660b76babd9a

## Requirements

- Google Chrome installed
- Google Custom Search JSON API Key and Code (optional if a URL is provided)
- OpenAi API Key
- Anthropic API Key

## App workflow

The main.py file contains a high-level description of the app's workflow.
As you can see, Miney uses Google search to find relevant websites; alternatively, you can also provide a URL to extract data from a specific website:

```python
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
```

The following diagram describes the app's workflow for each website visited (the previous for loop).
The pink hexagonal shapes represent actions or decisions made by an LLM. The orange slanted rectangle represents the user's input.
As you can see, Miney will first use LLM Vision to close any popups present in the page. Then, using the website's text, it will locate the HTML tags that contain data and
write a script to extract it. If the script doesn't run successfully, the LLM will be asked to rewrite it. Then the data extracted is validated by an LLM.
After this, if the user is not happy with the result the whole process can be repeated, incorporating feedback from the previous iteration:

![AI Workflow](https://github.com/user-attachments/assets/cb974f73-9a8d-4fcb-a939-a90ad32c7383)


## Data sample

You can view an example of some data extracted using Miney at my [Kaggle dataset](https://www.kaggle.com/datasets/terencicp/50-busiest-airports-by-passenger-traffic-2023).

## License

This project is licensed under the Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) license. You are free to share and adapt the code as long as you credit me, Terenci Claramunt, as the author, do not use it for commercial purposes, and distribute any modified content under the same license.

For more details, visit [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

## Disclaimer

Note that Miney is just a prototype; it can provide great results but sometimes it might get lost and confused.
Also note that given the probabilistic nature of LLMs a query that works perfectly might give terrible results on the next run.
A lot of work is still needed to turn Miney into a viable product.

This app is provided for educational and research purposes only. By using this software, you agree to the following:
- Respect for Website Owners: You will use this tool responsibly and respect the rights of website owners. Always check the website's robots.txt file and terms of service before scraping.
- Legal Compliance: You are solely responsible for ensuring that your use of this tool complies with all applicable local, state, national, and international laws and regulations.
- Ethical Use: This tool should not be used to gather personal information, violate privacy, or engage in any malicious activities.
- Rate Limiting: Implement appropriate rate limiting to avoid overloading target websites with requests.
- No Warranty: This software is provided "as is", without warranty of any kind. The authors are not responsible for any damages or legal issues arising from the use of this tool.
- Data Usage: Any data collected using this tool should be used in accordance with relevant data protection laws and ethical guidelines.

No usage data is collected while running the app.
