# aiji_bot.py
import sqlite3
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
import calendar
from flask import Flask
import os

# ============== 基础配置 ==============
TOKEN = os.getenv("TAAEGvHHzXwiA2Qq4c1ZEvjFu5i5JJ3ajzhs")  # 从环境变量获取
ADMIN_ID = int(os.getenv("1826555006"))  # 管理员ID
TIMEZONE = pytz.timezone("Asia/Shanghai")
DB_NAME = "data/aiji_live.db"  # 持久化路径
PORT = int(os.getenv("PORT", 8080))  # Render端口

# 品牌信息配置
BRAND_INFO = {
    "name": "爱即直播工作室",
    "slogan": "用心直播，爱即永恒",
    "min_hours": 2.5,
    "month_days": 22,
    "total_hours": 50,
    "admin_contact": "@Aiji_Admin"
}

# ============== Flask保活服务 ==============
app = Flask(__name__)

@app.route('/')
def home():
    return f"{BRAND_INFO['name']} 正常运行中 ✅"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# ============== 数据库初始化 ==============
def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS monthly_records
                 (user_id INTEGER,
                  year INTEGER,
                  month INTEGER,
                  valid_days INTEGER DEFAULT 0,
                  total_hours REAL DEFAULT 0.0,
                  daily_logs TEXT,
                  PRIMARY KEY(user_id, year, month))''')
                 
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  date TEXT,
                  start_time TEXT,
                  end_time TEXT,
                  duration REAL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS config
                 (id INTEGER PRIMARY KEY,
                  key TEXT UNIQUE,
                  value TEXT)''')
    
    conn.commit()
    conn.close()

init_db()
scheduler = AsyncIOScheduler(timezone=TIMEZONE)

# ============== 核心功能实现 ==============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = f"""
🌟 欢迎使用{BRAND_INFO['name']}智能管理系统！
━━━━━━━━━━━━━━━━━━━━
📢 {BRAND_INFO['slogan']}
━━━━━━━━━━━━━━━━━━━━
🕒 考勤标准：
1️⃣ 每日直播 ≥ {BRAND_INFO['min_hours']}小时
2️⃣ 每月有效天数 ≥ {BRAND_INFO['month_days']}天
3️⃣ 每月总时长 ≥ {BRAND_INFO['total_hours']}小时
━━━━━━━━━━━━━━━━━━━━
发送 /help 获取操作指南
"""
    await update.message.reply_text(welcome_msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = f"""
📚 {BRAND_INFO['name']}操作手册
━━━━━━━━━━━━━━━━━━━━
🎥 直播管理：
/live - 开始直播计时
/end  - 结束直播计时
/stats - 查看本月数据
━━━━━━━━━━━━━━━━━━━━
📊 数据要求：
• 每日最低直播：{BRAND_INFO['min_hours']}小时
• 每月有效天数：{BRAND_INFO['month_days']}天
• 每月总时长：{BRAND_INFO['total_hours']}小时
━━━━━━━━━━━━━━━━━━━━
📞 管理员联系：{BRAND_INFO['admin_contact']}
"""
    await update.message.reply_text(help_text)

# （后续直播管理、统计、定时任务等完整代码请参考之前提供的功能模块）

# ============== 启动程序 ==============
def main():
    # 启动Flask保活
    from threading import Thread
    Thread(target=run_flask).start()
    
    # 启动Telegram机器人
    application = Application.builder().token(TOKEN).build()
    
    # 注册命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    # 添加其他命令处理器...
    
    # 启动定时任务
    scheduler.start()
    application.run_polling()

if __name__ == "__main__":
    main()