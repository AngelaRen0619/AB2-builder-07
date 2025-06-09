#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Strands Agent - Personal Assistant

This script creates a personal assistant agent using Strands Agents SDK.
The agent can manage appointments using custom tools and built-in tools.
"""

import os
import sqlite3
import uuid
import json
from datetime import datetime, timedelta
import re
import sys
import traceback
import boto3
from strands import Agent, tool
from strands.models import BedrockModel

try:
    from strands import Agent, tool
    from strands.models import BedrockModel
except ImportError as e:
    print(f"错误: 无法导入 strands 模块。请确保已安装 strands-agents 包。")
    sys.exit(1)

try:
    from strands_tools import calculator, current_time, retrieve
except ImportError as e:
    print(f"错误: 无法导入 strands_tools 模块。请确保已安装 strands-agents-tools 包。")
    sys.exit(1)

try:
    from query_tools import handle_query
except ImportError as e:
    print(f"错误: 无法导入 query_tools 模块。")
    sys.exit(1)

try:
    import boto3
except ImportError as e:
    print(f"错误: 无法导入 boto3 模块。请确保已安装 boto3 包。")
    sys.exit(1)

# 导入数据库相关函数
try:
    from database_functions import extend_database_structure, initialize_meeting_rooms
except ImportError as e:
    print(f"错误: 无法导入数据库函数。")
    sys.exit(1)

# 导入工具函数
try:
    from tools import (
        find_available_rooms,
        book_meeting_room,
        list_meeting_rooms,
        create_appointment,
        list_appointments,
        cancel_appointment,
        update_appointment
    )
except ImportError as e:
    print(f"错误: 无法导入工具函数。")
    sys.exit(1)

def main():
    """
    Main function to create and run the personal assistant agent.
    """
    
    try:
        # 初始化数据库结构和会议室数据
        extend_database_structure()
        initialize_meeting_rooms()
        
        # 直接设置 Knowledge Base ID 和区域
        kb_id = "CQ8WAO4MYJ"  # 替换为你的知识库ID
        region = "us-east-1"  # 使用知识库所在的区域
        
        os.environ["KNOWLEDGE_BASE_ID"] = kb_id
        os.environ["AWS_DEFAULT_REGION"] = region
        
        # 检查 AWS 凭证
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials is None:
            print("错误: 未找到 AWS 凭证。请确保已配置 AWS CLI。")
            return
        
        print("AWS 凭证检查通过")
        
        # 测试知识库连接
        try:
            bedrock_client = boto3.client('bedrock-agent-runtime', region_name=region)
        except Exception as e:
            print(f"错误: 无法创建 bedrock-agent-runtime 客户端: {str(e)}")
            return
    
        # Define system prompt
        system_prompt = """你是一个有用的个人助理，专注于管理我的约会和日历，并提供常见信息查询服务。
你可以访问约会管理工具、计算器，并可以检查当前时间，帮助我有效组织日程安排。
你支持线上和线下会议预定。如果是线下会议，你会询问参会人数并帮我预定合适的会议室。
你可以帮助创建、查看、更新和取消约会，如果取消线下会议，你会同时取消相关的会议室预定。
始终提供约会ID，以便我可以在需要时更新或取消它。

你还能够处理各种常见查询，例如报销流程、考试券申请、办公室权限申请、GenAI相关知识、差旅预订等。
当我询问这些主题时，你会优先使用 handle_query 这个工具来快速查询，如果这个工具查不到需要的信息，则使用知识库检索工具(retrieve)来查找相关信息，并提供准确的答案。

使用知识库时的指导原则：
1. 优先使用retrieve工具搜索相关信息
2. 仔细分析检索结果，提供最相关的信息
3. 如果知识库中没有相关信息，告知用户并建议其他可能的帮助渠道
4. 保持回答简洁明了，重点突出关键信息"""

        # Define the model with region configuration
        try:
            model = BedrockModel(
                model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                max_tokens=64000,
                region=region,  # 指定Bedrock服务所在的区域
                additional_request_fields={
                    "thinking": {
                        "type": "disabled",
                    }
                },
            )
        except Exception as e:
            print(f"错误: 配置 Bedrock 模型失败: {str(e)}")
            return

        # Create the agent
        try:
            agent = Agent(
                model=model,
                system_prompt=system_prompt,
                tools=[
                    current_time,
                    calculator,
                    retrieve,  # 添加知识库检索工具
                    create_appointment,
                    list_appointments,
                    update_appointment,
                    cancel_appointment,
                    find_available_rooms,
                    book_meeting_room,
                    list_meeting_rooms,
                    handle_query,
                ],
            )
        except Exception as e:
            print(f"错误: 创建 Agent 失败: {str(e)}")
            return

        print("个人助理已就绪！")
        print("输入'exit'退出。")
        
        # 存储会话上下文
        conversation_context = {}
        
        # 交互循环
        while True:
            try:
                user_input = input("\n您: ")
                if user_input.lower() == 'exit':
                    break
                
                # 检查是否正在等待约会详情
                if 'waiting_for_appointment' in conversation_context:
                    # 解析输入作为约会详情
                    parts = user_input.split('，')
                    if len(parts) >= 3:
                        location = parts[0].strip()
                        title = parts[1].strip()
                        description = parts[2].strip()
                        date = conversation_context.get('date', '')
                        meeting_type = conversation_context.get('meeting_type', 'online')
                        attendees_count = conversation_context.get('attendees_count')
                        
                        if attendees_count:
                            attendees_count = int(attendees_count)
                        
                        # 创建约会
                        try:
                            result = create_appointment(date, title, description, meeting_type, location, attendees_count)
                            print(f"\n助理: 已成功创建约会！{result}")
                        except ValueError as e:
                            print(f"\n助理: 创建约会时出错: {str(e)}")
                        
                        # 清除上下文
                        conversation_context.clear()
                        continue
                    else:
                        print("\n助理: 请按照格式提供信息：地点，标题，描述")
                        continue
                try:
                    results = agent(user_input)
                except Exception as e:
                    print(f"\n助理: 处理请求时出错: {str(e)}")
                    continue
            
                # 检查响应是否询问约会详情
                last_assistant_message = None
                for message in agent.messages:
                    if message.get("role") == "assistant":
                        last_assistant_message = message
                
                response_text = ""
                if last_assistant_message:
                    for content_item in last_assistant_message.get("content", []):
                        if "text" in content_item:
                            response_text += content_item["text"]
                
                # 如果正在询问约会详情，设置上下文
                if "请提供约会的地点、标题和描述" in response_text:
                    # 尝试从响应中提取日期
                    date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', response_text)
                    if date_match:
                        date_str = date_match.group(1)
                        # 将中文日期格式转换为YYYY-MM-DD
                        date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
                        conversation_context['date'] = date_str + " 15:00"  # 默认为下午3点
                    
                    # 检查是否提到线下会议
                    if "线下会议" in response_text or "面对面会议" in response_text:
                        conversation_context['meeting_type'] = "offline"
                        
                        # 检查是否已提供参会人数
                        attendees_match = re.search(r'(\d+)\s*人', response_text)
                        if attendees_match:
                            conversation_context['attendees_count'] = attendees_match.group(1)
                    else:
                        conversation_context['meeting_type'] = "online"
                    
                    conversation_context['waiting_for_appointment'] = True
                
                # 打印响应
                print("\n助理:", end=" ")
                print(response_text)
            except UnicodeDecodeError:
                print("\n助理: 错误: 无法处理输入的中文字符。请尝试使用英文输入或使用 ./run.sh 脚本运行程序。")
                continue
            except Exception as e:
                print(f"\n助理: 发生错误: {str(e)}")
                continue
    except Exception as e:
        print(f"程序运行时发生错误: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
