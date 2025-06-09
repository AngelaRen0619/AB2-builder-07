#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Query Tools for Strands Agent - Personal Assistant

This module provides tools for handling common queries and returning appropriate links.
"""

from strands import tool


@tool
def handle_query(query: str) -> str:
    """
    处理常见查询并返回相应的链接
    
    Args:
        query (str): 用户的查询内容
        
    Returns:
        str: 包含相关链接的回复
    """
    # 将查询转为小写以进行不区分大小写的匹配
    query_lower = query.lower()
    
    # 定义查询关键词和对应的链接
    query_links = {
        "报销": {
            "link": "https://us2.concursolutions.com/home",
            "description": "报销相关需求"
        },
        "concur": {
            "link": "https://us2.concursolutions.com/home",
            "description": "报销相关需求"
        },
        "考试券": {
            "link": "https://sim.amazon.com/issues/create?template=9bf02270-082e-4f3b-9bb4-cfdbe57709ab",
            "description": "申请考试券/考证/半价券"
        },
        "考证": {
            "link": "https://sim.amazon.com/issues/create?template=9bf02270-082e-4f3b-9bb4-cfdbe57709ab",
            "description": "申请考试券/考证/半价券"
        },
        "半价券": {
            "link": "https://sim.amazon.com/issues/create?template=9bf02270-082e-4f3b-9bb4-cfdbe57709ab",
            "description": "申请考试券/考证/半价券"
        },
        "证书": {
            "link": "https://sim.amazon.com/issues/create?template=9bf02270-082e-4f3b-9bb4-cfdbe57709ab",
            "description": "申请考试券/考证/半价券"
        },
        "办公室权限": {
            "link": "https://t.corp.amazon.com/create/templates/3783318b-ae33-4c59-9d72-11b6bceec5a5",
            "description": "办公室权限申请"
        },
        "门禁": {
            "link": "https://t.corp.amazon.com/create/templates/3783318b-ae33-4c59-9d72-11b6bceec5a5",
            "description": "办公室权限申请"
        },
        "genai": {
            "link": "https://aws.highspot.com/items/66690d6ac011a8e67b540b4c?lfrm=rhp.0",
            "description": "GenAI相关知识查询"
        },
        "mcp server": {
            "link": "https://aws.highspot.com/items/66690d6ac011a8e67b540b4c?lfrm=rhp.0",
            "description": "GenAI相关知识查询"
        },
        "dify": {
            "link": "https://aws.highspot.com/items/66690d6ac011a8e67b540b4c?lfrm=rhp.0",
            "description": "GenAI相关知识查询" 
        },
        "q developer": {
            "link": "https://aws.highspot.com/items/66690d6ac011a8e67b540b4c?lfrm=rhp.0",
            "description": "GenAI相关知识查询"
        },
        "agentic ai": {
            "link": "https://aws.highspot.com/items/66690d6ac011a8e67b540b4c?lfrm=rhp.0",
            "description": "GenAI相关知识查询"
        },
        "strands agents": {
            "link": "https://aws.highspot.com/items/66690d6ac011a8e67b540b4c?lfrm=rhp.0",
            "description": "GenAI相关知识查询"
        },
        "nova": {
            "link": "https://aws.highspot.com/items/66690d6ac011a8e67b540b4c?lfrm=rhp.0", 
            "description": "GenAI相关知识查询"
        },
        "prompt caching": {
            "link": "https://aws.highspot.com/items/66690d6ac011a8e67b540b4c?lfrm=rhp.0",
            "description": "GenAI相关知识查询"
        },
        "飞机": {
            "link": "https://idp.federate.amazon.com/api/saml2/v1/idp-initiated?providerId=Amazon.bcdtravel.cn&target=%3cRELAY_STATE%3e",
            "description": "飞机、酒店预定等"
        },
        "机票": {
            "link": "https://idp.federate.amazon.com/api/saml2/v1/idp-initiated?providerId=Amazon.bcdtravel.cn&target=%3cRELAY_STATE%3e",
            "description": "飞机、酒店预定等"
        },
        "酒店": {
            "link": "https://idp.federate.amazon.com/api/saml2/v1/idp-initiated?providerId=Amazon.bcdtravel.cn&target=%3cRELAY_STATE%3e",
            "description": "飞机、酒店预定等"
        },
        "预订": {
            "link": "https://idp.federate.amazon.com/api/saml2/v1/idp-initiated?providerId=Amazon.bcdtravel.cn&target=%3cRELAY_STATE%3e",
            "description": "飞机、酒店预定等"
        },
        "出差": {
            "link": "https://idp.federate.amazon.com/api/saml2/v1/idp-initiated?providerId=Amazon.bcdtravel.cn&target=%3cRELAY_STATE%3e",
            "description": "飞机、酒店预定等"
        }
    }
    
    # 查找匹配的关键词
    for keyword, info in query_links.items():
        if keyword in query_lower:
            return f"针对您的「{info['description']}」需求，您可以访问以下链接：\n{info['link']}"
    
    # 如果没有匹配到任何关键词
    return "很抱歉，我目前还没有找到与您查询匹配的信息。我们正在不断完善查询库，请您稍后再试或者换一种方式描述您的需求。"
