#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google Analytics 博客访问统计脚本
用于获取 GA4 页面浏览量并更新 GitHub README 中的徽章
"""

import os
import re
import json
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest
from google.oauth2 import service_account

# 显示脚本开始执行的信息
print("===== 开始执行 Google Analytics 博客统计脚本 =====")

try:
    # 获取凭据和属性ID
    credentials_path = "credentials.json"
    property_id = os.environ.get("GA_PROPERTY_ID")
    
    # 打印配置信息（不显示敏感内容）
    print(f"使用的 GA4 属性 ID: {property_id}")
    
    # 显示服务账号信息（不显示敏感数据）
    with open(credentials_path, 'r') as f:
        creds_data = json.load(f)
        print(f"服务账号邮箱: {creds_data.get('client_email')}")
        print(f"服务账号项目 ID: {creds_data.get('project_id')}")
    
    # 创建凭据对象
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path, 
        scopes=["https://www.googleapis.com/auth/analytics.readonly"]
    )
    print("成功创建凭据对象")
    
    # 创建 GA4 API 客户端
    client = BetaAnalyticsDataClient(credentials=credentials)
    print("成功创建 GA4 API 客户端")
    
    # 创建 API 请求，获取总页面浏览量
    # GA4 中使用 screenPageViews 代替旧版的 pageviews
    request = RunReportRequest(
        property=f"properties/{property_id}",
        metrics=[{"name": "screenPageViews"}],
        date_ranges=[{"start_date": "2020-01-01", "end_date": "today"}]
    )
    print(f"准备请求数据，完整属性路径: properties/{property_id}")
    
    # 发送 API 请求并获取报告
    print("发送 GA4 API 请求...")
    response = client.run_report(request)
    print("成功接收 GA4 API 响应")
    
    # 提取总页面浏览量
    page_views = response.rows[0].metric_values[0].value
    print(f"获取到的总页面浏览量: {page_views}")
    
    # 格式化数字，使大数字更易读
    def format_number(num):
        num = int(num)
        if num >= 1000000:
            return f"{num/1000000:.1f}M"  # 百万级显示为 X.XM
        elif num >= 1000:
            return f"{num/1000:.1f}K"      # 千级显示为 X.XK
        else:
            return str(num)                # 小于1000直接显示数字
    
    # 格式化页面浏览量
    formatted_views = format_number(page_views)
    print(f"格式化后的页面浏览量: {formatted_views}")
    
    # 读取 README.md 文件
    print("准备更新 README.md 文件")
    with open("README.md", "r", encoding="utf-8") as file:
        content = file.read()
    
    # 定义要查找和替换的模式
    # 这里匹配博客访问量徽章的 URL
    pattern = r'<img src="https://img\.shields\.io/badge/Blog-Views-E65A65\.svg\?logo=google-analytics&logoColor=white"'
    replacement = f'<img src="https://img.shields.io/badge/Blog-{formatted_views}_Views-E65A65.svg?logo=google-analytics&logoColor=white"'
    
    # 使用正则表达式查找并替换徽章中的文本
    updated_content = re.sub(pattern, replacement, content)
    
    # 检查是否成功替换
    if updated_content == content:
        print("警告：未找到匹配的徽章模式，请检查 README.md 中的徽章格式")
        
        # 尝试使用更宽松的模式进行匹配
        pattern_alt = r'<img src="https://img\.shields\.io/badge/Blog-[^-]*-E65A65\.svg'
        replacement_alt = f'<img src="https://img.shields.io/badge/Blog-{formatted_views}_Views-E65A65.svg'
        updated_content = re.sub(pattern_alt, replacement_alt, content)
        
        if updated_content == content:
            print("仍然未找到匹配的徽章。尝试最宽松的匹配...")
            pattern_last = r'<img src="https://img\.shields\.io/badge/Blog-[^"]+"'
            replacement_last = f'<img src="https://img.shields.io/badge/Blog-{formatted_views}_Views-E65A65.svg?logo=google-analytics&logoColor=white"'
            updated_content = re.sub(pattern_last, replacement_last, content)
    
    # 将更新后的内容写回 README.md 文件
    with open("README.md", "w", encoding="utf-8") as file:
        file.write(updated_content)
    
    # 检查是否成功更新
    if updated_content != content:
        print(f"成功更新 README.md，博客访问量: {formatted_views}")
    else:
        print("警告：README.md 未更新，未找到匹配的徽章模式")
        
        # 打印当前徽章格式以便调试
        import re
        badge_pattern = r'<img src="https://img\.shields\.io/badge/Blog-[^"]+"'
        badges = re.findall(badge_pattern, content)
        print(f"在 README.md 中找到的徽章格式: {badges}")

except Exception as e:
    # 详细错误处理
    print(f"❌ 执行过程中发生错误: {str(e)}")
    
    # 提供错误类型和详细信息
    import traceback
    print("\n详细错误信息:")
    traceback.print_exc()
    
    # 如果是 API 相关错误，提供更具体的帮助信息
    error_str = str(e).lower()
    if "permission" in error_str or "403" in error_str:
        print("\n可能的解决方案:")
        print("1. 确保服务账号已添加到 Google Analytics 属性的访问管理中")
        print("2. 确保服务账号有足够的权限（至少为'查看者'）")
        print("3. 确保 Google Analytics Data API 已在 Google Cloud 项目中启用")
        print("4. 确保使用的是正确的属性 ID")
    elif "not found" in error_str or "404" in error_str:
        print("\n可能的解决方案:")
        print("1. 检查属性 ID 是否正确")
        print("2. 确保属性尚未被删除")
    
    # 退出并返回错误代码
    raise

else:
    # 成功完成
    print("✅ 脚本执行成功完成!")

