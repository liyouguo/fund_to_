import os
import sys
import logging
from email_sender import EmailSender

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# 配置邮件参数
os.environ['SMTP_SERVER'] = 'smtp.qq.com'
os.environ['SMTP_PORT'] = '465'
os.environ['SMTP_USER'] = '724429664@qq.com'
os.environ['SMTP_PASSWORD'] = 'rohrdfaljywhbfgf'
os.environ['RECIPIENTS'] = '724429664@qq.com'

# 创建测试CSV文件
import pandas as pd
import datetime

# 创建测试数据
test_data = {
    '基金代码': ['000001', '000002'],
    '基金名称': ['测试基金1', '测试基金2'],
    '基金类型': ['混合型', '股票型'],
    '净值日期': [datetime.datetime.now().strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d')],
    '布林带信号': ['买入', '卖出'],
    '报告日期': [datetime.datetime.now().strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d')]
}

test_df = pd.DataFrame(test_data)
test_csv_path = 'test_signal.csv'
test_df.to_csv(test_csv_path, index=False, encoding='utf-8-sig')

# 测试邮件发送
try:
    email_sender = EmailSender()
    result = email_sender.send_email(test_csv_path)
    print(f"邮件发送结果：{'成功' if result else '失败'}")
    
    # 测试SMTP连接
    print("\n测试SMTP连接：")
    result = email_sender.test_connection()
    print(f"SMTP连接测试结果：{'成功' if result else '失败'}")
except Exception as e:
    print(f"测试失败：{str(e)}")
    import traceback
    traceback.print_exc()
finally:
    # 清理测试文件
    if os.path.exists(test_csv_path):
        os.remove(test_csv_path)
