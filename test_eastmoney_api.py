#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试东方财富基金API的正则表达式提取功能
"""

import requests
import re
import json


def test_eastmoney_api():
    """测试东方财富基金API"""
    url = "http://fund.eastmoney.com/js/fundcode_search.js"
    print(f"开始测试东方财富API: {url}")
    
    try:
        # 发送请求
        response = requests.get(url, timeout=10)
        print(f"请求状态码: {response.status_code}")
        
        # 获取响应内容
        content = response.text
        print(f"响应内容长度: {len(content)}")
        
        # 使用正则表达式提取基金数组
        fund_array_match = re.search(r'var\s+r\s*=\s*(\[[\s\S]*?\])\s*;', content)
        if fund_array_match:
            fund_array_str = fund_array_match.group(1)
            print(f"提取的基金数组字符串长度: {len(fund_array_str)}")
            
            try:
                # 解析为Python列表
                fund_array = json.loads(fund_array_str)
                print(f"成功解析，基金数量: {len(fund_array)}")
                
                # 打印前10个基金数据
                print("\n前10个基金数据:")
                for i, fund in enumerate(fund_array[:10]):
                    if isinstance(fund, list) and len(fund) >= 5:
                        print(f"基金{i+1}: 代码={fund[0]}, 名称={fund[2]}, 类型={fund[3]}")
                
                # 构建基金字典示例
                fund_dict = {}
                for fund in fund_array:
                    if isinstance(fund, list) and len(fund) >= 5:
                        fund_dict[fund[0]] = {
                            "name": fund[2],
                            "type": fund[3]
                        }
                
                print(f"\n基金字典构建完成，共 {len(fund_dict)} 条记录")
                
                # 测试查询几个基金代码
                test_codes = ["000001", "000011", "000031", "110011"]
                print("\n测试查询基金代码:")
                for code in test_codes:
                    if code in fund_dict:
                        print(f"{code}: {fund_dict[code]['name']} - {fund_dict[code]['type']}")
                    else:
                        print(f"{code}: 未找到")
                
                return True
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                return False
        else:
            print("未找到基金数组")
            return False
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return False
    except Exception as e:
        print(f"其他错误: {e}")
        return False


if __name__ == "__main__":
    test_eastmoney_api()