# -*- coding: utf-8 -*-
import os
import sqlite3
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
from flask import Flask

# ============== 基础配置 ==============
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
TIMEZONE = pytz.timezone("Asia/Shanghai")
DATA_DIR = os.getenv("DATA_DIR", "/data")  # 通过环境变量配置路径
DB_NAME = os.path.join(DATA_DIR, "aiji_live.db")
PORT = int(os.getenv("PORT", 8080))

# 品牌配置
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
def health_check():
    return f"{BRAND_INFO['name']} 服务运行正常 | 当前时间: {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}"

# ============== 增强版数据库初始化 ==============
def init_db():
    conn = None
    try:
        # 自动创建数据目录（兼容所有环境）
        os.makedirs(DATA_DIR, exist_ok=True)
        logging.info(f"数据库目录已创建：{DATA_DIR}")
        
        # 初始化数据库连接
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # 配置表
        c.execute('''CREATE TABLE IF NOT EXISTS config
                     (id INTEGER PRIMARY KEY,
                     key TEXT UNIQUE,
                     value TEXT)''')
        
        # 月度记录表
        c.execute('''CREATE TABLE IF NOT EXISTS monthly_records
                     (user_id INTEGER,
                      year INTEGER,
                      month INTEGER,
                      valid_days INTEGER DEFAULT 0,
                      total_hours REAL DEFAULT 0.0,
                      daily_logs TEXT,
                      PRIMARY KEY(user_id, year, month))''')
        
        # 直播会话表
        c.execute('''CREATE TABLE IF NOT EXISTS sessions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      date TEXT,
                      start_time TEXT,
                      end_time TEXT,
                      duration REAL)''')
        
        conn.commit()
        logging.info("数据库表初始化完成")
        return conn
        
    except Exception as e:
        logging.error(f"数据库初始化失败: {str(e)}")
        # 紧急回退方案：使用内存数据库
        logging.warning("使用内存数据库作为临时解决方案")
        return sqlite3.connect(":memory:")
        
    finally:
        if conn:
            conn.close()

# ============== 机器人核心功能 ==============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = f"""
🌟 欢迎使用{BRAND_INFO['name']}智能考勤系统！
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
/end - 结束直播计时
/stats - 查看本月数据
━━━━━━━━━━━━━━━━━━━━
📞 管理员联系：{BRAND_INFO['admin_contact']}
"""
    await update.message.reply_text(help_text)

# ============== 主程序 ==============
def run_flask():
    app.run(host='0.0.0.0', port=PORT)

def main():
    # 初始化日志
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    
    # 启动数据库
    db_conn = init_db()
    db_conn.close()
    
    # 启动Flask保活
    from threading import Thread
    Thread(target=run_flask).start()
    
    # 启动机器人
    application = Application.builder().token(TOKEN).build()
    
    # 注册命令
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # 定时任务
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.start()
    
    application.run_polling()

if __name__ == "__main__":
    main()
