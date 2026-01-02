# 基金信号分析系统

## 项目简介

基金信号分析系统是一个自动化的基金技术分析工具，能够分析指定基金的技术指标，生成信号明细表格，并通过邮件发送分析报告。

## 功能特性

1. **技术指标计算**：
   - 移动平均线（MA5/MA10）
   - RSI指标
   - MACD指标
   - CCI指标
   - 布林带指标

2. **信号生成**：
   - 均线信号
   - RSI信号
   - MACD信号
   - CCI信号
   - 布林带信号

3. **报告输出**：
   - CSV格式信号明细
   - Excel格式信号明细
   - 运行日志记录

4. **邮件发送**：
   - 自动发送分析报告
   - 支持多收件人
   - HTML格式邮件正文
   - 信号明细附件

5. **自动化部署**：
   - GitHub Actions支持
   - 每日定时运行
   - 环境变量配置
   - 运行状态监控

## 项目结构

```
.
├── main.py                    # 主程序入口
├── logger.py                  # 日志记录模块
├── email_sender.py            # 邮件发送模块
├── requirements.txt           # 依赖列表
├── README.md                  # 项目文档
├── .gitignore                 # Git忽略文件
└── .github/
    └── workflows/
        └── daily_fund_analysis.yml  # GitHub Actions配置
```

## 安装和运行

### 环境要求

- Python 3.9+
- 依赖库：见requirements.txt

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行方式

#### 1. 基本运行

```bash
python main.py
```

#### 2. 自定义参数运行

```bash
# 保留最近5天的数据
python main.py --days 5

# 分析指定基金
python main.py --funds "000001,110022,710001"

# 使用问财选股（自然语言查询）
python main.py --wencai "场外基金近1年涨幅top200"

# 组合参数
python main.py --days 7 --wencai "股票型场外基金 近1年涨幅top100"

# 使用问财选股并指定保留天数
python main.py --wencai "场外基金近6个月涨幅top50" --days 10
```

#### 3. 测试邮件发送

```bash
python main.py --test-email
```

## 环境变量配置 

系统使用以下环境变量进行配置： 

| 环境变量名          | 描述                | 默认值          | 
|-------------------|---------------------|----------------| 
| SMTP_SERVER       | SMTP服务器地址       | smtp.qq.com    | 
| SMTP_PORT         | SMTP服务器端口       | 465            | 
| SMTP_USER         | SMTP用户名          |                | 
| SMTP_PASSWORD     | SMTP密码            |                | 
| RECIPIENTS        | 收件人列表，用分号分隔 |                | 
| WENCAI_QUERY      | 问财选股查询语句     | 场外基金近1年涨幅top200 | 

### GitHub Actions Secrets配置 

在GitHub Actions中，您需要在仓库的**Settings** > **Secrets and variables** > **Actions**中配置以下Secrets： 

| Secret名称        | 描述                | 值示例          | 
|------------------|---------------------|----------------| 
| SMTP_SERVER      | SMTP服务器地址       | smtp.qq.com    | 
| SMTP_PORT        | SMTP服务器端口       | 465            | 
| SMTP_USER        | SMTP用户名          | your@qq.com    | 
| SMTP_PASSWORD    | SMTP密码或授权码     | your_password  | 
| RECIPIENTS       | 收件人列表，用分号分隔 | recipient1@qq.com;recipient2@qq.com | 
| WENCAI_QUERY     | 问财选股查询语句     | 场外基金近1年涨幅top200 | 

### GitHub Actions 问财选股配置

要在GitHub Actions中使用问财选股功能，您可以修改`.github/workflows/main.yml`文件，添加问财查询参数：

```yaml
# 在run步骤中添加--wencai参数
run: |
  python main.py --days ${{ github.event.inputs.days_to_keep || 10 }} --wencai "场外基金近1年涨幅top200"
```

您也可以在手动触发工作流时通过输入参数指定问财查询语句：

1. 在工作流配置中添加inputs：
   ```yaml
   workflow_dispatch:
     inputs:
       days_to_keep:
         description: '保留数据天数'
         required: false
         default: '10'
       wencai_query:
         description: '问财选股查询语句，例如：场外基金近1年涨幅top200'
         required: false
         default: '场外基金近1年涨幅top200'
   ```

2. 在run步骤中使用输入参数：
   ```yaml
   run: |
     python main.py --days ${{ github.event.inputs.days_to_keep || 10 }} --wencai "${{ github.event.inputs.wencai_query || '场外基金近1年涨幅top200' }}"
   ``` 

**注意**：
- 对于QQ邮箱，SMTP_PASSWORD是QQ邮箱的授权码，而不是登录密码
- 确保您已开启QQ邮箱的SMTP服务
- 请严格按照上述Secret名称进行配置，不要使用其他名称

## 自动化部署

### GitHub Actions配置

1. Fork项目到你的GitHub仓库
2. 在仓库设置中添加以下Secrets：
   - SMTP_SERVER
   - SMTP_PORT
   - SMTP_USER
   - SMTP_PASSWORD
   - RECIPIENTS

3. GitHub Actions会在每日09:00（UTC时间，对应北京时间17:00）自动运行

### 手动触发

在GitHub Actions页面，可以手动触发工作流运行，并可选择保留天数。

## 输出文件

### 信号明细

- **CSV格式**：`output/信号明细_YYYY-MM-DD.csv`
- **Excel格式**：`output/信号明细_YYYY-MM-DD.xlsx`

### 运行日志

- **日志文件**：`logs/运行日志_YYYYMMDD_HHMMSS.log`
- **日志级别**：DEBUG/INFO/WARNING/ERROR
- **输出方式**：控制台和文件双重输出

## 邮件内容

### 主题格式

```
📊 基金布林带策略晨报 - YYYY-MM-DD
```

### 正文结构

1. **报告概览**
   - 报告日期
   - 分析基金数
   - 信号分布统计

2. **操作建议**
   - 买入信号操作建议
   - 卖出信号操作建议
   - 持有信号操作建议

3. **风险提示**
   - 技术指标局限性
   - 市场风险提示
   - 投资建议声明

4. **附件**
   - 完整的信号明细表格

## 风险提示

1. 本系统仅提供技术分析参考，不构成投资建议
2. 基金投资有风险，入市需谨慎
3. 技术指标存在滞后性，需结合基本面分析
4. 市场波动较大时，信号可能不准确

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或Pull Request。
