import os
import sqlite3
import uuid
import json
from datetime import datetime, timedelta

def extend_database_structure():
    """扩展数据库结构，添加会议类型和会议室相关表"""
    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()
    
    # 1. 检查appointments表中是否有meeting_type字段
    cursor.execute("PRAGMA table_info(appointments)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "meeting_type" not in columns:
        cursor.execute("ALTER TABLE appointments ADD COLUMN meeting_type TEXT DEFAULT 'online'")
    
    # 2. 创建会议室表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meeting_rooms (
        room_id TEXT PRIMARY KEY,
        name TEXT,
        location TEXT,
        capacity INTEGER
    )
    """)
    
    # 3. 创建会议室预定表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS room_bookings (
        booking_id TEXT PRIMARY KEY,
        room_id TEXT,
        appointment_id TEXT,
        booking_date TEXT,
        start_time TEXT,
        end_time TEXT,
        attendees_count INTEGER,
        status TEXT,
        FOREIGN KEY (room_id) REFERENCES meeting_rooms (room_id),
        FOREIGN KEY (appointment_id) REFERENCES appointments (id)
    )
    """)
    
    conn.commit()
    conn.close()

def initialize_meeting_rooms():
    """初始化北京和上海的会议室数据"""
    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()
    
    # 检查是否已初始化
    try:
        cursor.execute("SELECT COUNT(*) FROM meeting_rooms")
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return f"已存在{count}间会议室，无需重新初始化"
    except sqlite3.OperationalError:
        # 表不存在，继续初始化
        pass
    
    # 北京会议室 - 20间
    rooms = []
    for i in range(1, 21):
        # 设置不同容量
        if i <= 4:
            capacity = 2
        elif i <= 10:
            capacity = 3 + (i % 2)  # 3-4人
        elif i <= 15:
            capacity = 5 + (i % 2)  # 5-6人
        elif i <= 18:
            capacity = 7 + (i % 2)  # 7-8人
        else:
            capacity = 9 + (i % 2)  # 9-10人
        
        room_id = f"BJ-{i:02d}"
        name = f"北京A-{i:02d}"
        rooms.append((room_id, name, "北京", capacity))
    
    # 上海会议室 - 20间
    for i in range(1, 21):
        if i <= 4:
            capacity = 2
        elif i <= 10:
            capacity = 3 + (i % 2)
        elif i <= 15:
            capacity = 5 + (i % 2)
        elif i <= 18:
            capacity = 7 + (i % 2)
        else:
            capacity = 9 + (i % 2)
        
        room_id = f"SH-{i:02d}"
        name = f"上海B-{i:02d}"
        rooms.append((room_id, name, "上海", capacity))
    
    cursor.executemany(
        "INSERT INTO meeting_rooms (room_id, name, location, capacity) VALUES (?, ?, ?, ?)", 
        rooms
    )
    
    # 创建一些示例预定
    create_sample_bookings(cursor)
    
    conn.commit()
    conn.close()
    return f"已成功初始化{len(rooms)}间会议室"

def create_sample_bookings(cursor):
    """创建一些示例预定记录"""
    # 确保表存在
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS room_bookings (
        booking_id TEXT PRIMARY KEY,
        room_id TEXT,
        appointment_id TEXT,
        booking_date TEXT,
        start_time TEXT,
        end_time TEXT,
        attendees_count INTEGER,
        status TEXT,
        FOREIGN KEY (room_id) REFERENCES meeting_rooms (room_id)
    )
    """)
    
    today = datetime.now()
    bookings = []
    
    # 为北京的几个会议室创建预定
    for i in range(1, 6):
        booking_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        booking_id = f"BOOK-BJ-{i}-{uuid.uuid4().hex[:8]}"
        room_id = f"BJ-{(i*2):02d}"
        
        # 上午预定
        bookings.append((
            booking_id,
            room_id,
            "sample-appointment-id",
            booking_date,
            "09:00",
            "11:00",
            i + 2,
            "confirmed"
        ))
        
        # 下午预定
        booking_id = f"BOOK-BJ-{i+5}-{uuid.uuid4().hex[:8]}"
        bookings.append((
            booking_id,
            room_id,
            "sample-appointment-id",
            booking_date,
            "14:00",
            "16:00",
            i + 2,
            "confirmed"
        ))
    
    # 为上海的几个会议室创建预定
    for i in range(1, 6):
        booking_date = (today + timedelta(days=i+1)).strftime("%Y-%m-%d")
        booking_id = f"BOOK-SH-{i}-{uuid.uuid4().hex[:8]}"
        room_id = f"SH-{(i*3):02d}"
        
        bookings.append((
            booking_id,
            room_id,
            "sample-appointment-id",
            booking_date,
            "10:00",
            "12:00",
            i + 3,
            "confirmed"
        ))
    
    cursor.executemany(
        "INSERT INTO room_bookings (booking_id, room_id, appointment_id, booking_date, start_time, end_time, attendees_count, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        bookings
    )
