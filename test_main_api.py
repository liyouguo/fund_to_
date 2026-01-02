#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试main.py中的基金API功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath("./fund_signal_system"))

from main import FundSignalAnalyzer


def test_main_api():
    """测试main.py中的基金API功能"""
    print("开始测试main.py中的基金API功能")
    
    try:
        # 创建FundSignalAnalyzer实例
        fss = FundSignalAnalyzer()
        
        # 测试fetch_fund_data_from_api方法
        print("\n1. 测试fetch_fund_data_from_api方法:")
        fund_dict = fss.fetch_fund_data_from_api()
        print(f"获取到的基金数量: {len(fund_dict)}")
        
        # 测试几个基金代码
        test_codes = ["000001", "000011", "000031", "110011", "510300"]
        print("\n2. 测试get_fund_basic_info方法:")
        for code in test_codes:
            try:
                name, fund_type = fss.get_fund_basic_info(code)
                print(f"基金{code}: 名称={name}, 类型={fund_type}")
            except Exception as e:
                print(f"获取基金{code}信息失败: {e}")
        
        print("\n测试完成!")
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_main_api()