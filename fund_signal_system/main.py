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
import pywencai
warnings.filterwarnings('ignore')

class FundSignalAnalyzer:
    """基金信号分析器"""
    
    # 示例基金代码列表
    DEFAULT_FUND_CODES = [
    # 宽基核心
    "110020.OF",
    "001051.OF", 
    
    
    # 半导体/高端制造/
]
    
    def __init__(self):
        """初始化基金信号分析器"""
        self.report_date = datetime.now().strftime('%Y-%m-%d')
        self.email_sender = EmailSender()
        logger.info(f"初始化基金信号分析器，报告日期：{self.report_date}")
    

    
    def get_funds_from_wencai(self, query_content="场外基金近1年涨幅top100，混合类"):
        """使用问财选股获取基金列表和详细信息"""
        logger.info(f"开始使用问财选股获取基金列表，查询条件：{query_content}")
        
        try:
            # 自动翻页查询场外基金数据
            logger.info("调用pywencai.get()函数获取数据...")
            fund_data = pywencai.get(
                query=query_content,
                query_type="fund",  # 指定查询类型为基金
                loop=True,  # 自动循环分页，获取所有页数据
                perpage=100,  # 每页最大100条
                sleep=1,  # 每页请求间隔1秒
                log=True,  # 打印请求日志
            )
            
            logger.info(f"pywencai.get()返回结果类型：{type(fund_data)}")
            
            if fund_data is None:
                logger.error("pywencai.get()返回None")
                return None
            
            if isinstance(fund_data, pd.DataFrame):
                logger.info(f"问财返回DataFrame，共 {len(fund_data)} 条记录")
                logger.info(f"返回数据列名：{list(fund_data.columns)}")
                
                # 打印返回数据的前几行，方便调试
                if not fund_data.empty:
                    logger.info(f"返回数据前3行：\n{fund_data.head(3)}")
                    # 打印完整的列名和部分字段值
                    logger.info("\n=== 详细数据列信息 ===")
                    for i, col in enumerate(fund_data.columns):
                        sample_value = fund_data[col].iloc[0] if len(fund_data) > 0 else "N/A"
                        logger.info(f"{i+1}. 列名：{col}，示例值：{sample_value}")
                
                # 检查数据是否为空
                if fund_data.empty:
                    logger.error("问财返回的数据为空DataFrame")
                    return None
                
                # 查找基金代码相关的列
                fund_code_cols = [col for col in fund_data.columns if '代码' in col or 'code' in col.lower()]
                logger.info(f"找到可能的基金代码列：{fund_code_cols}")
                
                if not fund_code_cols:
                    logger.error("问财返回数据中未找到基金代码相关字段")
                    return None
                
                # 使用找到的第一个基金代码列
                fund_code_col = fund_code_cols[0]
                logger.info(f"使用 {fund_code_col} 作为基金代码列")
                
                # 确保去掉".OF"后缀，兼容带完整格式的基金代码
                fund_data['基金代码'] = fund_data[fund_code_col].astype(str).str.split('.').str[0]
                
                # 查找并添加基金简称
                fund_name_cols = [col for col in fund_data.columns if '简称' in col or '名称' in col]
                if fund_name_cols:
                    fund_name_col = fund_name_cols[0]
                    # 将基金简称列重命名为统一的'基金简称'
                    if fund_name_col != '基金简称':
                        fund_data.rename(columns={fund_name_col: '基金简称'}, inplace=True)
                    logger.info(f"使用 {fund_name_col} 作为基金简称列")
                else:
                    logger.warning("问财返回数据中未找到基金简称相关字段")
                    # 添加默认的基金简称
                    fund_data['基金简称'] = fund_data['基金代码'].apply(lambda x: f"基金{x}")
                
                # 查找并添加投资类型
                invest_type_cols = [col for col in fund_data.columns if '投资类型' in col or '类型' in col]
                if invest_type_cols:
                    invest_type_col = invest_type_cols[0]
                    # 将投资类型列重命名为统一的'投资类型'
                    if invest_type_col != '投资类型':
                        fund_data.rename(columns={invest_type_col: '投资类型'}, inplace=True)
                    logger.info(f"使用 {invest_type_col} 作为投资类型列")
                else:
                    logger.warning("问财返回数据中未找到投资类型相关字段")
                    # 添加默认的投资类型
                    fund_data['投资类型'] = "未知类型"
                
                logger.info(f"获取到基金数据：{list(fund_data['基金代码'])[:10]}...(共{len(fund_data)}个)")
                logger.info(f"基金数据包含字段：{list(fund_data.columns)}")
                return fund_data
            else:
                logger.error(f"问财返回的不是DataFrame，而是 {type(fund_data)}")
                logger.error(f"返回数据：{fund_data}")
                return None
                
        except Exception as e:
            logger.error(f"问财选股失败：{str(e)}")
            logger.error(f"异常类型：{type(e).__name__}")
            logger.error(f"异常详情：{repr(e)}")
            # 打印堆栈信息
            import traceback
            logger.error(f"堆栈信息：{traceback.format_exc()}")
            return None
    

    
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
        """获取基金历史净值数据，带重试机制"""
        def retry_api_call(func, max_retries=3, base_delay=1):
            """API调用重试装饰器"""
            for attempt in range(max_retries):
                try:
                    return func()
                except Exception as e:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"第{attempt+1}次尝试失败，{delay:.2f}秒后重试：{str(e)}")
                        time.sleep(delay)
                    else:
                        logger.error(f"第{attempt+1}次尝试失败，放弃重试：{str(e)}")
                        raise
        
        try:
            logger.info(f"开始获取基金{fund_code}历史数据")
            
            # 处理基金代码，去掉.OF后缀
            if '.' in fund_code:
                base_code = fund_code.split('.')[0]
                logger.debug(f"基金代码{fund_code}去掉后缀后为{base_code}")
                fund_code = base_code
            
            # 尝试使用fund_open_fund_info_em获取历史数据
            try:
                # 获取基金历史数据，带重试机制
                def get_history_data():
                    return ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
                
                history_df = retry_api_call(get_history_data, max_retries=3, base_delay=1)
                
                if history_df is not None and not history_df.empty:
                    # 基金简称将从问财返回值获取，这里先使用默认值
                    fund_name = f"基金{fund_code}"
                    
                    # 添加基金代码和简称
                    history_df['基金代码'] = fund_code
                    history_df['基金简称'] = fund_name
                    
                    # 重命名列以匹配原有结构
                    history_df = history_df.rename(columns={
                        '单位净值': '最新净值',
                        '日增长率': '日增长率%'
                    })
                    
                    # 确保日增长率是数值类型
                    history_df['日增长率%'] = pd.to_numeric(history_df['日增长率%'], errors='coerce')
                    
                    logger.info(f"基金{fund_code}历史数据获取成功，共{len(history_df)}条记录")
                    return history_df
            except Exception as e:
                logger.error(f"使用fund_open_fund_info_em获取基金{fund_code}历史数据失败：{str(e)}")
                logger.warning(f"基金{fund_code}遇到JavaScript解析错误，尝试使用备选方案")
            
            # 备选方案：使用fund_open_fund_daily_em获取当日数据
            def get_daily_data():
                return ak.fund_open_fund_daily_em()
            
            df = retry_api_call(get_daily_data, max_retries=3, base_delay=1)
            
            if df is None:
                logger.warning(f"基金数据返回为空")
                return None
            
            # 筛选当前基金的数据
            fund_data = df[df['基金代码'] == fund_code]
            if fund_data.empty:
                logger.warning(f"未找到基金{fund_code}的数据")
                return None
            
            # 基金简称将从问财返回值获取，这里先使用默认值
            fund_name = f"基金{fund_code}"
            
            # 动态获取最新净值列名
            unit_nav_col = [col for col in df.columns if '-单位净值' in col][0]
            unit_nav = fund_data.iloc[0][unit_nav_col]
            daily_growth = fund_data.iloc[0]['日增长率']
            
            # 从列名中提取日期
            latest_date = unit_nav_col.split('-')[0]
            
            # 创建历史数据结构
            history_data = pd.DataFrame({
                '净值日期': [pd.Timestamp(latest_date)],
                '最新净值': [float(unit_nav)],
                '日增长率%': [float(daily_growth)],
                '基金代码': [fund_code],
                '基金简称': [fund_name]
            })
            
            logger.info(f"基金{fund_code}数据获取成功，共{len(history_data)}条记录")
            return history_data
            
        except Exception as e:
            logger.error(f"获取基金{fund_code}历史数据失败：{str(e)}")
            return None
    
    def calculate_technical_indicators(self, df):
        """计算技术指标和信号"""
        if df is None or len(df) == 0:
            logger.warning(f"数据为空，无法计算技术指标")
            return df
        
        fund_code = df['基金代码'].iloc[0] if '基金代码' in df.columns else '未知'
        logger.info(f"开始计算基金{fund_code}技术指标和信号")
        
        # 简单处理：如果数据不足20条，只生成基础信号
        if len(df) < 20:
            logger.info(f"基金{fund_code}数据不足20条，生成基础信号")
            
            # 添加基础信号列
            df['均线信号'] = '持有'
            df['RSI'] = 50  # 默认RSI值
            df['RSI信号'] = '持有'
            df['MACD'] = 0  # 默认MACD值
            df['macd值'] = 0
            df['macd信号'] = '持有'
            df['cci值'] = 0  # 默认CCI值
            df['cci信号'] = '持有'
            df['布林带中轨值'] = df['最新净值']
            df['布林带上轨值'] = df['最新净值'] * 1.1
            df['布林带下轨值'] = df['最新净值'] * 0.9
            df['布林带信号'] = '持有'
            
            logger.info(f"基金{fund_code}基础信号生成完成")
            return df
        
        # 原有代码：数据足够时计算完整技术指标
        logger.debug("数据足够，计算完整技术指标")
        
        # 计算移动平均线和均线信号
        df['MA5'] = df['最新净值'].rolling(window=5, min_periods=1).mean()
        df['MA10'] = df['最新净值'].rolling(window=10, min_periods=1).mean()
        df['均线信号'] = '持有'
        buy_signals = (df['MA5'] > df['MA10']) & (df['MA5'].shift(1) <= df['MA10'].shift(1))
        sell_signals = (df['MA5'] < df['MA10']) & (df['MA5'].shift(1) >= df['MA10'].shift(1))
        df.loc[buy_signals, '均线信号'] = '买入'
        df.loc[sell_signals, '均线信号'] = '卖出'
        logger.info(f"均线信号生成完成：买入信号{buy_signals.sum()}个，卖出信号{sell_signals.sum()}个")
        
        # 计算RSI和RSI信号
        delta = df['最新净值'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss
        df['RSI'] = (100 - (100 / (1 + rs))).round(2)
        df['RSI'] = df['RSI'].fillna(50)
        df['RSI信号'] = '持有'
        rsi_buy = (df['RSI'] > 30) & (df['RSI'].shift(1) <= 30)
        rsi_sell = (df['RSI'] < 70) & (df['RSI'].shift(1) >= 70)
        df.loc[rsi_buy, 'RSI信号'] = '买入'
        df.loc[rsi_sell, 'RSI信号'] = '卖出'
        logger.info(f"RSI信号生成完成：买入信号{rsi_buy.sum()}个，卖出信号{rsi_sell.sum()}个")
        
        # 计算MACD和MACD信号
        exp1 = df['最新净值'].ewm(span=12, adjust=False).mean()
        exp2 = df['最新净值'].ewm(span=26, adjust=False).mean()
        df['MACD'] = (exp1 - exp2).round(4)
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['macd值'] = df['MACD']
        df['macd信号'] = '持有'
        macd_buy = (df['MACD'] > -100) & (df['MACD'].shift(1) <= -100)
        macd_sell = (df['MACD'] < 100) & (df['MACD'].shift(1) >= 100)
        df.loc[macd_buy, 'macd信号'] = '买入'
        df.loc[macd_sell, 'macd信号'] = '卖出'
        logger.info(f"MACD信号生成完成：买入信号{macd_buy.sum()}个，卖出信号{macd_sell.sum()}个")
        
        # 计算CCI和CCI信号
        tp = df['最新净值']
        tp_ma = tp.rolling(window=20, min_periods=1).mean()
        md = tp.rolling(window=20, min_periods=1).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
        df['cci值'] = ((tp - tp_ma) / (0.015 * md)).round(2)
        df['cci值'] = df['cci值'].fillna(0)
        df['cci信号'] = '持有'
        cci_buy = (df['cci值'] > -100) & (df['cci值'].shift(1) <= -100)
        cci_sell = (df['cci值'] < 100) & (df['cci值'].shift(1) >= 100)
        df.loc[cci_buy, 'cci信号'] = '买入'
        df.loc[cci_sell, 'cci信号'] = '卖出'
        logger.info(f"CCI信号生成完成：买入信号{cci_buy.sum()}个，卖出信号{cci_sell.sum()}个")
        
        # 计算布林带和布林带信号
        df['布林带中轨值'] = df['最新净值'].rolling(window=20, min_periods=1).mean()
        bb_std = df['最新净值'].rolling(window=20, min_periods=1).std()
        df['布林带上轨值'] = (df['布林带中轨值'] + 2 * bb_std).round(4)
        df['布林带下轨值'] = (df['布林带中轨值'] - 2 * bb_std).round(4)
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
            '基金代码', '基金简称', '投资类型', '净值日期',
            '均线信号', 'RSI', 'RSI信号', 'cci值', 'cci信号',
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
            # 确保净值日期是datetime类型
            output_df['净值日期'] = pd.to_datetime(output_df['净值日期'], errors='coerce')
            # 格式化为字符串
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
                'fund_name': fund_df['基金简称'].iloc[0],
                'signal_data': signal_df,
                'raw_data': fund_df
            }
            
        except Exception as e:
            logger.error(f"分析基金{fund_code}失败：{str(e)}")
            return None
    
    def run(self, days_to_keep=10, fund_codes=None, wencai_query=None):
        """运行基金信号分析"""
        logger.info("=" * 80)
        logger.info("基金信号分析系统开始运行")
        logger.info(f"报告日期：{self.report_date}")
        logger.info(f"保留天数：{days_to_keep}")
        logger.info("=" * 80)
        
        # 初始化问财基金数据
        wencai_fund_data = None
        
        # 使用问财选股获取基金列表和详细信息
        if wencai_query:
            wencai_fund_data = self.get_funds_from_wencai(wencai_query)
            if wencai_fund_data is not None:
                # 从问财数据中获取基金代码列表
                fund_codes = wencai_fund_data['基金代码'].tolist()
                logger.info(f"从问财获取到 {len(fund_codes)} 个基金")
            else:
                logger.error("问财选股未返回有效基金列表，使用默认基金列表")
                fund_codes = self.DEFAULT_FUND_CODES
        # 使用传入的基金代码或默认基金代码
        elif fund_codes is None:
            fund_codes = self.DEFAULT_FUND_CODES
            logger.info(f"使用默认基金列表，共{len(fund_codes)}个基金")
        
        logger.info(f"待分析基金代码：{fund_codes[:10]}...(共{len(fund_codes)}个)")
        
        # 初始化结果存储
        results = []
        
        # 创建输出目录，使用绝对路径确保在任何环境下都能正确访问
        output_dir = os.path.join(os.getcwd(), 'output')
        logger.info(f"输出目录绝对路径：{output_dir}")
        if not os.path.exists(output_dir):
            logger.info(f"创建输出目录：{output_dir}")
            os.makedirs(output_dir, exist_ok=True)
        else:
            logger.info(f"输出目录已存在：{output_dir}")
        
        # 初始化CSV和Excel文件，使用绝对路径
        csv_filename = os.path.join(output_dir, f'信号明细_{self.report_date}.csv')
        excel_filename = os.path.join(output_dir, f'信号明细_{self.report_date}.xlsx')
        logger.info(f"CSV文件路径：{csv_filename}")
        logger.info(f"Excel文件路径：{excel_filename}")
        
        # 初始化标志，用于判断是否是第一次写入
        first_write = True
        
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
                    signal_df['净值日期'] = pd.to_datetime(signal_df['净值日期'])
                    max_date = signal_df['净值日期'].max()
                    cutoff_date = max_date - pd.Timedelta(days=days_to_keep)
                    filtered_count = len(signal_df[signal_df['净值日期'] >= cutoff_date])
                    logger.info(f"基金{fund_code}数据过滤：{filtered_count}/{len(signal_df)}条记录保留")
                    
                    signal_df = signal_df[signal_df['净值日期'] >= cutoff_date]
                    signal_df['净值日期'] = signal_df['净值日期'].dt.strftime('%Y-%m-%d')
                
                # 从问财数据中更新基金简称和投资类型
                if wencai_fund_data is not None:
                    # 查找当前基金在问财数据中的信息
                    fund_info = wencai_fund_data[wencai_fund_data['基金代码'] == fund_code]
                    if not fund_info.empty:
                        # 更新基金简称
                        fund_name = fund_info['基金简称'].iloc[0]
                        signal_df['基金简称'] = fund_name
                        logger.info(f"更新基金{fund_code}简称为：{fund_name}")
                        
                        # 更新投资类型
                        if '投资类型' in fund_info.columns:
                            invest_type = fund_info['投资类型'].iloc[0]
                            signal_df['投资类型'] = invest_type
                            logger.info(f"更新基金{fund_code}投资类型为：{invest_type}")
                
                # 立即写入信号数据到CSV文件
                logger.info(f"开始写入基金{fund_code}信号数据到CSV文件")
                if first_write:
                    # 第一次写入，包含表头
                    signal_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    first_write = False
                else:
                    # 后续写入，追加数据，不包含表头
                    signal_df.to_csv(csv_filename, index=False, encoding='utf-8-sig', mode='a', header=False)
                logger.debug(f"基金{fund_code}信号数据已写入CSV文件：{csv_filename}")
                
                # 立即写入信号数据到Excel文件
                logger.info(f"开始写入基金{fund_code}信号数据到Excel文件")
                try:
                    if os.path.exists(excel_filename):
                        # 文件已存在，读取现有数据并追加
                        with pd.ExcelFile(excel_filename, engine='openpyxl') as xls:
                            existing_df = pd.read_excel(xls, sheet_name='信号明细')
                        combined_df = pd.concat([existing_df, signal_df], ignore_index=True)
                    else:
                        # 文件不存在，直接写入
                        combined_df = signal_df
                    
                    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                        combined_df.to_excel(writer, sheet_name='信号明细', index=False)
                    logger.debug(f"基金{fund_code}信号数据已写入Excel文件：{excel_filename}")
                except Exception as e:
                    logger.error(f"写入Excel文件失败：{str(e)}")
                    logger.debug(f"异常详情：{repr(e)}")
            else:
                logger.warning(f"基金{fund_code}分析失败，跳过")
            
            # 避免请求过快，使用2-3秒的随机间隔
            import random
            sleep_time = random.uniform(1, 1.5)
            logger.debug(f"等待{sleep_time:.2f}秒，避免API请求过快")
            time.sleep(sleep_time)
        
        elapsed_time = time.time() - start_time
        sys.stdout.write("\n")
        logger.info("=" * 80)
        logger.info(f"分析完成！成功: {len(results)}/{len(fund_codes)}")
        logger.info(f"总耗时: {elapsed_time:.1f}秒")
        logger.info("=" * 80)
        
        if not results:
            logger.error("没有成功分析任何基金，程序退出")
            return False
        
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
    """主函数，带完善的异常处理"""
    try:
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='基金信号分析系统')
        parser.add_argument('--days', type=int, default=10, help='保留数据天数')
        parser.add_argument('--funds', type=str, help='基金代码列表，用逗号分隔')
        parser.add_argument('--wencai', type=str, help='问财选股查询语句，例如：场外基金近1年涨幅top100，基金类型，c类')
        parser.add_argument('--test-email', action='store_true', help='测试邮件发送')
        args = parser.parse_args()
        
        # 初始化分析器
        analyzer = FundSignalAnalyzer()
        
        # 测试邮件发送
        if args.test_email:
            logger.info("开始测试邮件发送")
            test_csv = None
            try:
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
            except Exception as e:
                logger.error(f"测试邮件发送失败：{str(e)}")
                logger.debug(f"异常详情：{repr(e)}")
                import traceback
                logger.error(f"堆栈信息：{traceback.format_exc()}")
            finally:
                # 确保无论是否发生异常，测试文件都会被删除
                if test_csv and os.path.exists(test_csv):
                    try:
                        os.remove(test_csv)
                        logger.info(f"测试文件 {test_csv} 已删除")
                    except Exception as e:
                        logger.warning(f"删除测试文件 {test_csv} 失败：{str(e)}")
            # 将return语句移到finally块外面
            return
        
        # 解析基金代码列表
        fund_codes = None
        if args.funds:
            try:
                fund_codes = args.funds.split(',')
                logger.info(f"从命令行参数获取基金代码列表：{fund_codes}")
            except Exception as e:
                logger.error(f"解析基金代码列表失败：{str(e)}")
                logger.debug(f"异常详情：{repr(e)}")
                return
        
        # 从命令行参数或环境变量中获取问财查询语句
        wencai_query = args.wencai
        if not wencai_query:
            wencai_query = os.environ.get('WENCAI_QUERY')
            if wencai_query:
                logger.info(f"从环境变量获取问财查询语句：{wencai_query}")
        
        # 运行分析
        logger.info("开始运行基金信号分析")
        analyzer.run(days_to_keep=args.days, fund_codes=fund_codes, wencai_query=wencai_query)
        
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序运行失败：{str(e)}")
        logger.debug(f"异常详情：{repr(e)}")
        import traceback
        logger.error(f"堆栈信息：{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
