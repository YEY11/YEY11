import os
import json
import re
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest

# 设置凭据
credentials_json = os.environ.get('GA_CREDENTIALS')
with open('credentials.json', 'w') as f:
    f.write(credentials_json)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'credentials.json'

# 初始化客户端
client = BetaAnalyticsDataClient()
property_id = os.environ.get('GA_PROPERTY_ID')

# 获取总页面浏览量
request = RunReportRequest(
    property=f"properties/{property_id}",
    metrics=[{"name": "screenPageViews"}],
    date_ranges=[{"start_date": "2020-01-01", "end_date": "today"}],
)
response = client.run_report(request)

# 提取数据
total_views = response.rows[0].metric_values[0].value
formatted_views = f"{int(total_views)/1000:.1f}K" if int(total_views) >= 1000 else total_views

# 更新README.md
with open('README.md', 'r') as file:
    content = file.read()

# 使用正则表达式替换徽章URL
updated_content = re.sub(
    r'<img src="https://img\.shields\.io/badge/[^"]+"', 
    f'<img src="https://img.shields.io/badge/Blog-{formatted_views}%20Views-E65A65.svg?logo=google-analytics&logoColor=white"', 
    content,
    count=1  # 只替换第一个匹配项，避免替换其他徽章
)

with open('README.md', 'w') as file:
    file.write(updated_content)

print(f"Updated blog stats to {formatted_views} views")
