import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from datetime import datetime
from logger import logger

class EmailSender:
    """邮件发送器"""
    
    def __init__(self):
        """初始化邮件发送器"""
        self.config = self._load_config()
    
    def _load_config(self):
        """加载邮件配置"""
        # 打印所有邮件相关的环境变量，用于调试
        logger.debug(f"SMTP_SERVER环境变量: '{os.environ.get('SMTP_SERVER')}'")
        logger.debug(f"SMTP_PORT环境变量: '{os.environ.get('SMTP_PORT')}'")
        logger.debug(f"SMTP环境变量: '{os.environ.get('SMTP')}'")
        logger.debug(f"SMTP_USER环境变量: '{os.environ.get('SMTP_USER')}'")
        logger.debug(f"SMTP_PASSWORD环境变量: '{os.environ.get('SMTP_PASSWORD')}'")
        logger.debug(f"RECIPIENTS环境变量: '{os.environ.get('RECIPIENTS')}'")
        
        # 处理SMTP端口 - 同时检查SMTP_PORT和SMTP环境变量
        smtp_port_env = os.environ.get('SMTP_PORT')
        if not smtp_port_env or not smtp_port_env.strip():
            # 如果SMTP_PORT为空，尝试使用SMTP环境变量
            smtp_port_env = os.environ.get('SMTP')
            logger.debug(f"使用SMTP环境变量作为端口: '{smtp_port_env}'")
        
        smtp_port = 465
        if smtp_port_env and smtp_port_env.strip():
            try:
                smtp_port = int(smtp_port_env.strip())
            except ValueError:
                # 如果转换失败，使用默认值
                logger.warning(f"无效的SMTP端口值: {smtp_port_env}，使用默认值465")
                smtp_port = 465
        
        # 确保SMTP服务器地址有效
        smtp_server = os.environ.get('SMTP_SERVER')
        logger.debug(f"初始SMTP_SERVER: '{smtp_server}'")
        
        if smtp_server is None or not smtp_server.strip():
            # 显式设置默认值，确保不为空
            smtp_server = 'smtp.qq.com'
            logger.warning(f"SMTP_SERVER环境变量为空或未设置，使用默认值: {smtp_server}")
        else:
            smtp_server = smtp_server.strip()
        
        logger.debug(f"最终SMTP_SERVER: '{smtp_server}'")
        
        return {
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'smtp_user': os.environ.get('SMTP_USER', ''),
            'smtp_password': os.environ.get('SMTP_PASSWORD', ''),
            'recipients': [r.strip() for r in os.environ.get('RECIPIENTS', '').split(';') if r.strip()]
        }
    
    def send_email(self, signal_csv_path, report_date=None):
        """发送基金信号报告邮件"""
        if report_date is None:
            report_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"开始发送基金信号报告邮件，报告日期：{report_date}")
        
        try:
            # 检查配置
            if not self.config['smtp_user'] or not self.config['smtp_password']:
                logger.error("SMTP配置不完整，无法发送邮件")
                return False
            
            if not self.config['recipients']:
                logger.error("收件人列表为空，无法发送邮件")
                return False
            
            # 创建邮件
            msg = MIMEMultipart()
            
            # 设置邮件主题和发件人
            msg['Subject'] = f"📊 基金布林带策略晨报 - {report_date}"
            msg['From'] = self.config['smtp_user']
            msg['To'] = ','.join(self.config['recipients'])
            
            # 读取信号数据，生成报告概览
            import pandas as pd
            signal_df = pd.read_csv(signal_csv_path)
            
            # 统计信号
            signal_counts = signal_df['布林带信号'].value_counts().to_dict()
            buy_signals = signal_counts.get('买入', 0) + signal_counts.get('机会买入', 0)
            sell_signals = signal_counts.get('卖出', 0) + signal_counts.get('提示风险', 0)
            hold_signals = signal_counts.get('持有', 0)
            
            # 生成HTML格式的邮件正文
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #2c3e50;">📊 基金布林带策略晨报</h2>
                <div style="margin-bottom: 20px;">
                    <strong>报告日期：</strong>{report_date}<br>
                    <strong>分析基金数：</strong>{signal_df['基金代码'].nunique()}<br>
                    <strong>信号分布：</strong>
                    <ul>
                        <li>买入信号：<span style="color: #27ae60;">{buy_signals}个</span></li>
                        <li>卖出信号：<span style="color: #e74c3c;">{sell_signals}个</span></li>
                        <li>持有信号：<span style="color: #f39c12;">{hold_signals}个</span></li>
                    </ul>
                </div>
                
                <h3 style="color: #2c3e50;">操作建议</h3>
                <div style="margin-bottom: 20px;">
                    <ol>
                        <li>对于出现"买入"或"机会买入"信号的基金，建议关注其基本面，考虑逐步建仓</li>
                        <li>对于出现"卖出"或"提示风险"信号的基金，建议评估持仓，考虑减仓或止盈</li>
                        <li>对于"持有"信号的基金，建议继续观察，等待明确信号</li>
                    </ol>
                </div>
                
                <h3 style="color: #2c3e50;">风险提示</h3>
                <div style="margin-bottom: 20px;">
                    <ol>
                        <li>技术指标仅供参考，不构成投资建议</li>
                        <li>市场波动较大，建议结合基本面分析</li>
                        <li>基金投资有风险，入市需谨慎</li>
                    </ol>
                </div>
                
                <p style="color: #7f8c8d;">祝投资顺利！</p>
            </body>
            </html>
            """
            
            # 添加正文
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 添加附件
            with open(signal_csv_path, 'rb') as f:
                attachment = MIMEApplication(f.read())
                attachment.add_header('Content-Disposition', f'attachment; filename={os.path.basename(signal_csv_path)}')
                msg.attach(attachment)
            
            # 发送邮件
            logger.info(f"连接SMTP服务器：{self.config['smtp_server']}:{self.config['smtp_port']}")
            server = smtplib.SMTP_SSL(self.config['smtp_server'], self.config['smtp_port'])
            logger.debug("SMTP服务器连接成功")
            
            logger.debug(f"登录SMTP服务器：{self.config['smtp_user']}")
            server.login(self.config['smtp_user'], self.config['smtp_password'])
            logger.debug("SMTP服务器登录成功")
            
            logger.debug(f"发送邮件给：{','.join(self.config['recipients'])}")
            server.send_message(msg)
            logger.debug("邮件发送成功")
            
            server.quit()
            logger.debug("SMTP服务器连接已关闭")
            
            logger.info(f"邮件发送成功，收件人：{','.join(self.config['recipients'])}")
            logger.info(f"附件：{signal_csv_path}")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件失败：{str(e)}")
            return False
    
    def test_connection(self):
        """测试SMTP连接"""
        try:
            logger.info("测试SMTP连接")
            server = smtplib.SMTP_SSL(self.config['smtp_server'], self.config['smtp_port'])
            server.login(self.config['smtp_user'], self.config['smtp_password'])
            server.quit()
            logger.info("SMTP连接测试成功")
            return True
        except Exception as e:
            logger.error(f"SMTP连接测试失败：{str(e)}")
            return False
