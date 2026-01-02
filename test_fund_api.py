import requests
import json

# 测试基金数据接口
url = "https://m.1234567.com.cn/data/FundSuggestList.js"

print(f"正在请求接口：{url}")
try:
    response = requests.get(url, timeout=10)
    print(f"请求状态码：{response.status_code}")
    
    # 处理响应内容
    content = response.text
    print(f"响应内容长度：{len(content)}")
    import re
    import json

    

    # # 方法1：提取整个 Datas 数组
    datas_match = re.search(r'"Datas":\s*(\[[\s\S]*?\])', content)
    if datas_match:
        datas_str = datas_match.group(1)
        
        
        # 将字符串解析为 Python 列表
        try:
            datas_list = json.loads(datas_str)
           
            for i, fund in enumerate(datas_list, 1):
                print(f"{fund}")
        except json.JSONDecodeError:
            print("无法直接解析为 JSON，使用正则提取")
            
            # 方法2：直接提取所有基金信息
            funds = re.findall(r'"([^"]+)"', datas_str)
            print(f"\n=== 共找到 {len(funds)} 个基金 ===")
            for i, fund in enumerate(funds, 1):
                print(f"{fund}")

       
        
except Exception as e:
    print(f"请求失败：{str(e)}")
    import traceback
    traceback.print_exc()
