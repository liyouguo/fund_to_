import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import time
import sys
import os
import argparse
from logger import logger
from email_sender import EmailSender
warnings.filterwarnings('ignore')

class FundSignalAnalyzer:
    """基金信号分析器"""
    
    # 示例基金代码列表
    DEFAULT_FUND_CODES = [
    # 宽基核心
    "110020.OF",
    "001051.OF", 
    "160119.OF",
    "011612.OF",
    "161725.OF",
    "003096.OF",
    "006327.OF",
    "161005.OF",
    "260108.OF",
    
    # 半导体/高端制造/业绩驱动
    "025208.OF",
    "025209.OF",
    "016370.OF",
    "016371.OF",
    "002112.OF",
    "001412.OF",
    "004320.OF",
    "007113.OF",
    "007114.OF",
    "008528.OF",
    "011452.OF",
    "011900.OF",
    "011899.OF",
    "015576.OF",
    "005903.OF",
    "001956.OF",
    "519618.OF",
    "003659.OF",
    "162201.OF",
    "257070.OF",
    "001170.OF",
    "016579.OF",
    "009025.OF",
    "009024.OF",
    "017612.OF",
    "740001.OF",
    "020026.OF",
    "519606.OF",
    "015593.OF",
    "018291.OF",
    "002125.OF",
    "025499.OF",
    "025500.OF",
    "006502.OF",
    "006503.OF",
    "001480.OF",
    "021528.OF",
    "010237.OF",
    "011891.OF",
    "011892.OF",
    "010238.OF",
    "006265.OF",
    "001438.OF",
    "001437.OF",
    "006887.OF",
    "006888.OF",
    "007382.OF",
    "014915.OF",
    "007381.OF",
    "014916.OF",
    "025704.OF",
    "005967.OF",
    "519005.OF",
    "016773.OF",
    "016772.OF",
    "010115.OF",
    "011412.OF",
    "001753.OF",
    "020440.OF",
    "017491.OF",
    "017490.OF",
    "020441.OF",
    "005090.OF",
    "005091.OF",
    "016873.OF",
    "016874.OF",
    "016013.OF",
    "009242.OF",
    "009243.OF",
    "016014.OF",
    "010415.OF",
    "011370.OF",
    "011369.OF",
    "010416.OF",
    "001613.OF",
    "017462.OF",
    "018611.OF",
    "018612.OF",
    "013250.OF",
    "021957.OF",
    "006167.OF",
    "006168.OF",
    "009645.OF",
    "009644.OF",
    "014023.OF",
    "290008.OF",
    "026245.OF",
    "024459.OF",
    "024460.OF",
    "009432.OF",
    "009433.OF",
    "018956.OF",
    "018957.OF",
    "014191.OF",
    "014192.OF",
    "022446.OF"
]
    
    def __init__(self):
        """初始化基金信号分析器"""
        self.report_date = datetime.now().strftime('%Y-%m-%d')
        self.email_sender = EmailSender()
        logger.info(f"初始化基金信号分析器，报告日期：{self.report_date}")
    
    def get_fund_basic_info(self, fund_code="000001"):
        """获取基金基本信息"""
        try:
            logger.debug(f"开始获取基金{fund_code}基本信息")
            fund_list_df = ak.fund_name_em()
            logger.debug(f"获取基金列表成功，共{len(fund_list_df)}条记录")
            
            fund_info = fund_list_df[fund_list_df['基金代码'] == fund_code]
            
            if not fund_info.empty:
                fund_name = fund_info.iloc[0]['基金简称']
                fund_type = fund_info.iloc[0]['基金类型']
                logger.debug(f"基金{fund_code}基本信息获取成功：名称={fund_name}, 类型={fund_type}")
                return fund_name, fund_type
            logger.warning(f"基金{fund_code}基本信息未找到")
            return f"基金{fund_code}", "未知类型"
        except Exception as e:
            logger.error(f"获取基金{fund_code}基本信息失败：{str(e)}")
            return f"基金{fund_code}", "未知类型"
    
    def show_progress(self, current, total, start_time, prefix="分析进度"):
        """显示分析进度"""
        elapsed_time = time.time() - start_time
        progress = current / total * 100
        
        if current > 0:
            remaining_time = (elapsed_time / current) * (total - current)
            time_str = f"预计剩余: {remaining_time:.1f}秒"
        else:
            time_str = ""
        
        sys.stdout.write(f"\r{prefix}: {current}/{total} ({progress:.1f}%) {time_str}")
        sys.stdout.flush()
    
    def get_fund_data(self, fund_code="000001"):
        """获取基金历史净值数据"""
        try:
            logger.info(f"开始获取基金{fund_code}历史数据")
            
            # 获取原始数据 - 使用新的接口函数替代fund_open_fund_info_em
            logger.debug(f"调用akshare获取基金{fund_code}历史净值数据")
            df = ak.fund_open_fund_hist_net_value(fund=fund_code)
            
            if df is None:
                logger.warning(f"基金{fund_code}返回数据为空")
                return None
            
            logger.debug(f"原始数据获取成功，共{len(df)}条记录")
            logger.debug(f"原始数据字段：{list(df.columns)}")
            
            if len(df) <= 20:
                logger.warning(f"基金{fund_code}数据不足20条（仅{len(df)}条），无法进行技术分析")
                return None
            
            # 数据清洗和处理
            logger.debug("开始数据清洗和处理")
            
            # 检查并处理不同的字段名
            if '净值日期' not in df.columns and 'date' in df.columns:
                df = df.rename(columns={'date': '净值日期'})
            if '单位净值' not in df.columns and 'net_value' in df.columns:
                df = df.rename(columns={'net_value': '单位净值'})
            if '日增长率' not in df.columns and 'change_rate' in df.columns:
                df = df.rename(columns={'change_rate': '日增长率'})
            
            df['净值日期'] = pd.to_datetime(df['净值日期'])
            logger.debug("净值日期转换为datetime类型完成")
            
            df = df.sort_values('净值日期').reset_index(drop=True)
            logger.debug("按净值日期排序完成")
            
            df = df.rename(columns={'单位净值': '最新净值', '日增长率': '日增长率%'})
            logger.debug("字段重命名完成")
            
            # 添加基金基本信息
            logger.debug("添加基金基本信息")
            fund_name, fund_type = self.get_fund_basic_info(fund_code)
            df['基金代码'] = fund_code
            df['基金名称'] = fund_name
            df['基金类型'] = fund_type
            logger.debug(f"基金基本信息添加完成：代码={fund_code}, 名称={fund_name}, 类型={fund_type}")
            
            logger.info(f"基金{fund_code}数据获取成功，共{len(df)}条记录")
            logger.debug(f"最终数据字段：{list(df.columns)}")
            
            return df
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"获取基金{fund_code}历史数据失败：{error_msg}")
            logger.debug(f"异常详情：{repr(e)}")
            
            # 特别处理akshare的JavaScript解析错误，记录后继续处理其他基金
            if "Unknown JavaScript error during parse" in error_msg:
                logger.warning(f"基金{fund_code}遇到JavaScript解析错误，这可能是由于网页结构变化导致的，跳过该基金")
            
            return None
    
    def calculate_technical_indicators(self, df):
        """计算技术指标和信号"""
        if df is None or len(df) < 20:
            logger.warning(f"数据不足或为空，无法计算技术指标")
            return df
        
        fund_code = df['基金代码'].iloc[0] if '基金代码' in df.columns else '未知'
        logger.info(f"开始计算基金{fund_code}技术指标和信号")
        
        # 计算移动平均线和均线信号
        logger.debug("计算移动平均线指标")
        df['MA5'] = df['最新净值'].rolling(window=5, min_periods=1).mean()
        df['MA10'] = df['最新净值'].rolling(window=10, min_periods=1).mean()
        logger.debug("MA5和MA10计算完成")
        
        logger.debug("生成均线信号")
        df['均线信号'] = '持有'
        buy_signals = (df['MA5'] > df['MA10']) & (df['MA5'].shift(1) <= df['MA10'].shift(1))
        sell_signals = (df['MA5'] < df['MA10']) & (df['MA5'].shift(1) >= df['MA10'].shift(1))
        df.loc[buy_signals, '均线信号'] = '买入'
        df.loc[sell_signals, '均线信号'] = '卖出'
        logger.info(f"均线信号生成完成：买入信号{buy_signals.sum()}个，卖出信号{sell_signals.sum()}个")
        
        # 计算RSI和RSI信号
        logger.debug("计算RSI指标")
        delta = df['最新净值'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss
        df['RSI'] = (100 - (100 / (1 + rs))).round(2)
        df['RSI'] = df['RSI'].fillna(50)
        logger.debug(f"RSI计算完成，当前值：{df['RSI'].iloc[-1]}")
        
        logger.debug("生成RSI信号")
        df['RSI信号'] = '持有'
        rsi_buy = (df['RSI'] > 30) & (df['RSI'].shift(1) <= 30)
        rsi_sell = (df['RSI'] < 70) & (df['RSI'].shift(1) >= 70)
        df.loc[rsi_buy, 'RSI信号'] = '买入'
        df.loc[rsi_sell, 'RSI信号'] = '卖出'
        logger.info(f"RSI信号生成完成：买入信号{rsi_buy.sum()}个，卖出信号{rsi_sell.sum()}个")
        
        # 计算MACD和MACD信号
        logger.debug("计算MACD指标")
        exp1 = df['最新净值'].ewm(span=12, adjust=False).mean()
        exp2 = df['最新净值'].ewm(span=26, adjust=False).mean()
        df['MACD'] = (exp1 - exp2).round(4)
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        logger.debug(f"MACD计算完成，当前值：{df['MACD'].iloc[-1]}")
        
        logger.debug("生成MACD信号")
        df['macd值'] = df['MACD']
        df['macd信号'] = '持有'
        macd_buy = (df['MACD'] > -100) & (df['MACD'].shift(1) <= -100)
        macd_sell = (df['MACD'] < 100) & (df['MACD'].shift(1) >= 100)
        df.loc[macd_buy, 'macd信号'] = '买入'
        df.loc[macd_sell, 'macd信号'] = '卖出'
        logger.info(f"MACD信号生成完成：买入信号{macd_buy.sum()}个，卖出信号{macd_sell.sum()}个")
        
        # 计算CCI和CCI信号
        logger.debug("计算CCI指标")
        tp = df['最新净值']
        tp_ma = tp.rolling(window=20, min_periods=1).mean()
        md = tp.rolling(window=20, min_periods=1).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
        df['cci值'] = ((tp - tp_ma) / (0.015 * md)).round(2)
        df['cci值'] = df['cci值'].fillna(0)
        logger.debug(f"CCI计算完成，当前值：{df['cci值'].iloc[-1]}")
        
        logger.debug("生成CCI信号")
        df['cci信号'] = '持有'
        cci_buy = (df['cci值'] > -100) & (df['cci值'].shift(1) <= -100)
        cci_sell = (df['cci值'] < 100) & (df['cci值'].shift(1) >= 100)
        df.loc[cci_buy, 'cci信号'] = '买入'
        df.loc[cci_sell, 'cci信号'] = '卖出'
        logger.info(f"CCI信号生成完成：买入信号{cci_buy.sum()}个，卖出信号{cci_sell.sum()}个")
        
        # 计算布林带和布林带信号
        logger.debug("计算布林带指标")
        df['布林带中轨值'] = df['最新净值'].rolling(window=20, min_periods=1).mean()
        bb_std = df['最新净值'].rolling(window=20, min_periods=1).std()
        df['布林带上轨值'] = (df['布林带中轨值'] + 2 * bb_std).round(4)
        df['布林带下轨值'] = (df['布林带中轨值'] - 2 * bb_std).round(4)
        logger.debug(f"布林带计算完成，当前中轨：{df['布林带中轨值'].iloc[-1]}")
        
        logger.debug("生成布林带信号")
        df['布林带信号'] = '持有'
        bb_buy_opp = df['最新净值'] < df['布林带下轨值']
        bb_risk = df['最新净值'] > df['布林带上轨值']
        bb_cross_buy = (df['最新净值'] > df['布林带下轨值']) & (df['最新净值'].shift(1) <= df['布林带下轨值'].shift(1))
        bb_cross_sell = (df['最新净值'] < df['布林带上轨值']) & (df['最新净值'].shift(1) >= df['布林带上轨值'].shift(1))
        
        df.loc[bb_buy_opp, '布林带信号'] = '机会买入'
        df.loc[bb_risk, '布林带信号'] = '提示风险'
        df.loc[bb_cross_buy, '布林带信号'] = '买入'
        df.loc[bb_cross_sell, '布林带信号'] = '卖出'
        
        logger.info(f"布林带信号生成完成：机会买入{bb_buy_opp.sum()}个，提示风险{bb_risk.sum()}个，")
        logger.info(f"穿越买入{bb_cross_buy.sum()}个，穿越卖出{bb_cross_sell.sum()}个")
        
        # 记录最终信号分布
        logger.debug("记录最终信号分布")
        if '净值日期' in df.columns:
            latest_date = df['净值日期'].max().strftime('%Y-%m-%d')
            latest_df = df[df['净值日期'] == df['净值日期'].max()]
            if not latest_df.empty:
                signals_summary = {
                    '均线信号': latest_df['均线信号'].iloc[0],
                    'RSI信号': latest_df['RSI信号'].iloc[0],
                    'macd信号': latest_df['macd信号'].iloc[0],
                    'cci信号': latest_df['cci信号'].iloc[0],
                    '布林带信号': latest_df['布林带信号'].iloc[0]
                }
                logger.info(f"基金{fund_code}在{latest_date}的最终信号：{signals_summary}")
        
        logger.info(f"基金{fund_code}技术指标计算和信号生成完成")
        return df
    
    def create_signal_table(self, df, fund_code):
        """创建信号明细表格"""
        if df is None or len(df) == 0:
            logger.warning(f"基金{fund_code}数据为空，无法创建信号表格")
            return pd.DataFrame()
        
        logger.info(f"开始创建基金{fund_code}信号明细表格")
        
        # 只保留信号相关字段
        logger.debug("定义需要保留的字段列表")
        required_columns = [
            '基金代码', '基金名称', '基金类型', '净值日期',
            '均线信号', 'RSI', 'RSI信号', 'MACD', 'cci值', 'cci信号',
            'macd值', 'macd信号', '布林带下轨值', '布林带中轨值',
            '布林带上轨值', '布林带信号'
        ]
        
        # 检查哪些字段存在
        logger.debug("检查数据中存在的字段")
        existing_columns = [col for col in required_columns if col in df.columns]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.warning(f"基金{fund_code}缺少以下字段：{missing_columns}")
        logger.info(f"保留字段：{existing_columns}")
        
        # 创建输出DataFrame
        logger.debug("创建信号表格副本")
        output_df = df[existing_columns].copy()
        logger.debug(f"信号表格创建成功，初始行数：{len(output_df)}")
        
        # 格式化日期
        if '净值日期' in output_df.columns:
            logger.debug("格式化净值日期为字符串格式")
            output_df['净值日期'] = output_df['净值日期'].dt.strftime('%Y-%m-%d')
        
        # 添加报告日期
        logger.debug(f"添加报告日期：{self.report_date}")
        output_df['报告日期'] = self.report_date
        
        logger.info(f"基金{fund_code}信号明细表格创建完成，共{len(output_df)}条记录")
        logger.debug(f"最终表格字段：{list(output_df.columns)}")
        
        return output_df
    
    def analyze_fund(self, fund_code, index, total, start_time):
        """分析单个基金"""
        self.show_progress(index, total, start_time, "分析进度")
        
        try:
            logger.info(f"开始分析基金：{fund_code}")
            
            # 获取基金数据
            fund_df = self.get_fund_data(fund_code)
            if fund_df is None:
                logger.warning(f"基金{fund_code}数据获取失败，跳过")
                return None
            
            # 计算技术指标
            fund_df = self.calculate_technical_indicators(fund_df)
            
            # 创建信号表格
            signal_df = self.create_signal_table(fund_df, fund_code)
            
            logger.info(f"基金{fund_code}分析完成")
            
            return {
                'fund_code': fund_code,
                'fund_name': fund_df['基金名称'].iloc[0],
                'signal_data': signal_df,
                'raw_data': fund_df
            }
            
        except Exception as e:
            logger.error(f"分析基金{fund_code}失败：{str(e)}")
            return None
    
    def run(self, days_to_keep=10, fund_codes=None):
        """运行基金信号分析"""
        logger.info("=" * 80)
        logger.info("基金信号分析系统开始运行")
        logger.info(f"报告日期：{self.report_date}")
        logger.info(f"保留天数：{days_to_keep}")
        logger.info("=" * 80)
        
        # 使用默认基金代码或传入的基金代码
        if fund_codes is None:
            fund_codes = self.DEFAULT_FUND_CODES
            logger.info(f"使用默认基金列表，共{len(fund_codes)}个基金")
        else:
            logger.info(f"使用自定义基金列表，共{len(fund_codes)}个基金")
        
        logger.info(f"待分析基金代码：{fund_codes}")
        
        # 初始化结果存储
        all_signal_data = []
        results = []
        
        # 开始分析
        start_time = time.time()
        logger.info("开始分析基金...")
        
        for i, fund_code in enumerate(fund_codes, 1):
            logger.debug(f"开始分析第{i}/{len(fund_codes)}个基金：{fund_code}")
            result = self.analyze_fund(fund_code, i, len(fund_codes), start_time)
            
            if result is not None:
                logger.debug(f"基金{fund_code}分析成功，添加到结果列表")
                results.append(result)
                
                # 过滤近N天的数据
                signal_df = result['signal_data'].copy()
                
                if '净值日期' in signal_df.columns:
                    logger.debug(f"过滤基金{fund_code}近{days_to_keep}天的数据")
                    signal_df['净值日期'] = pd.to_datetime(signal_df['净值日期'])
                    max_date = signal_df['净值日期'].max()
                    cutoff_date = max_date - pd.Timedelta(days=days_to_keep)
                    logger.debug(f"最大日期：{max_date.strftime('%Y-%m-%d')}，截止日期：{cutoff_date.strftime('%Y-%m-%d')}")
                    
                    filtered_count = len(signal_df[signal_df['净值日期'] >= cutoff_date])
                    logger.info(f"基金{fund_code}数据过滤：{filtered_count}/{len(signal_df)}条记录保留")
                    
                    signal_df = signal_df[signal_df['净值日期'] >= cutoff_date]
                    signal_df['净值日期'] = signal_df['净值日期'].dt.strftime('%Y-%m-%d')
                
                all_signal_data.append(signal_df)
                logger.debug(f"基金{fund_code}信号数据已添加到总列表")
            else:
                logger.warning(f"基金{fund_code}分析失败，跳过")
            
            # 避免请求过快
            logger.debug("等待0.5秒，避免API请求过快")
            time.sleep(0.5)
        
        elapsed_time = time.time() - start_time
        sys.stdout.write("\n")
        logger.info("=" * 80)
        logger.info(f"分析完成！成功: {len(results)}/{len(fund_codes)}")
        logger.info(f"总耗时: {elapsed_time:.1f}秒")
        logger.info("=" * 80)
        
        if not results:
            logger.error("没有成功分析任何基金，程序退出")
            return False
        
        # 合并信号数据
        logger.info("开始合并所有基金信号数据")
        logger.debug(f"共有{len(all_signal_data)}个基金的信号数据需要合并")
        combined_signals = pd.concat(all_signal_data, ignore_index=True)
        logger.info(f"信号数据合并完成，共{len(combined_signals)}行")
        
        # 创建输出目录
        output_dir = 'output'
        logger.debug(f"检查输出目录：{output_dir}")
        if not os.path.exists(output_dir):
            logger.info(f"创建输出目录：{output_dir}")
            os.makedirs(output_dir)
        else:
            logger.debug(f"输出目录已存在：{output_dir}")
        
        # 生成信号CSV文件
        logger.info("开始生成信号明细CSV文件")
        csv_filename = os.path.join(output_dir, f'信号明细_{self.report_date}.csv')
        combined_signals.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        logger.info(f"信号明细CSV已生成：{csv_filename}")
        logger.debug(f"CSV文件大小：{os.path.getsize(csv_filename)}字节")
        
        # 生成Excel文件
        logger.info("开始生成信号明细Excel文件")
        excel_filename = os.path.join(output_dir, f'信号明细_{self.report_date}.xlsx')
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            combined_signals.to_excel(writer, sheet_name='信号明细', index=False)
        logger.info(f"信号明细Excel已生成：{excel_filename}")
        logger.debug(f"Excel文件大小：{os.path.getsize(excel_filename)}字节")
        
        # 发送邮件
        logger.info("开始发送邮件通知")
        email_sent = self.email_sender.send_email(csv_filename, self.report_date)
        if email_sent:
            logger.info("邮件发送成功")
        else:
            logger.error("邮件发送失败")
        
        logger.info("=" * 80)
        logger.info("基金信号分析系统运行完成")
        logger.info("=" * 80)
        
        return True

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='基金信号分析系统')
    parser.add_argument('--days', type=int, default=10, help='保留数据天数')
    parser.add_argument('--funds', type=str, help='基金代码列表，用逗号分隔')
    parser.add_argument('--test-email', action='store_true', help='测试邮件发送')
    args = parser.parse_args()
    
    # 初始化分析器
    analyzer = FundSignalAnalyzer()
    
    # 测试邮件发送
    if args.test_email:
        logger.info("开始测试邮件发送")
        # 创建测试文件
        test_df = pd.DataFrame({
            '基金代码': ['000001'],
            '基金名称': ['测试基金'],
            '基金类型': ['混合型'],
            '净值日期': ['2026-01-01'],
            '布林带信号': ['买入'],
            '报告日期': [analyzer.report_date]
        })
        test_csv = f'test_signal_{analyzer.report_date}.csv'
        test_df.to_csv(test_csv, index=False, encoding='utf-8-sig')
        
        # 发送测试邮件
        analyzer.email_sender.send_email(test_csv, analyzer.report_date)
        
        # 删除测试文件
        if os.path.exists(test_csv):
            os.remove(test_csv)
        
        return
    
    # 解析基金代码列表
    fund_codes = None
    if args.funds:
        fund_codes = args.funds.split(',')
    
    # 运行分析
    analyzer.run(days_to_keep=args.days, fund_codes=fund_codes)

if __name__ == "__main__":
    main()