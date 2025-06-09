from strands import tool
import json
import sqlite3
from datetime import datetime, timedelta
import uuid

@tool
def find_available_rooms(date: str, start_time: str, end_time: str, location: str, attendees_count: int) -> str:
    """
    查找指定条件下的可用会议室
    
    Args:
        date (str): 预定日期 (YYYY-MM-DD格式)
        start_time (str): 开始时间 (HH:MM格式)
        end_time (str): 结束时间 (HH:MM格式)
        location (str): 地点 (如"北京"或"上海")
        attendees_count (int): 参会人数
    
    Returns:
        str: 可用会议室的JSON格式列表
    """
    conn = sqlite3.connect("appointments.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 查找该地点所有容量足够的会议室
    cursor.execute(
        "SELECT * FROM meeting_rooms WHERE location = ? AND capacity >= ? ORDER BY capacity",
        (location, attendees_count)
    )
    
    suitable_rooms = [dict(row) for row in cursor.fetchall()]
    
    if not suitable_rooms:
        conn.close()
        return "[]"  # 没有足够容量的会议室
    
    # 检查已有的预定
    available_rooms = []
    for room in suitable_rooms:
        # 检查时间冲突
        cursor.execute("""
        SELECT * FROM room_bookings 
        WHERE room_id = ? AND booking_date = ? AND 
        ((start_time <= ? AND end_time > ?) OR
         (start_time < ? AND end_time >= ?) OR
         (start_time >= ? AND end_time <= ?))
        """, (
            room['room_id'], date, 
            end_time, start_time,  # 检查预定开始于我们结束之前
            end_time, start_time,  # 检查预定结束于我们开始之后
            start_time, end_time   # 检查预定完全在我们的时间段内
        ))
        
        conflicts = cursor.fetchall()
        if not conflicts:
            available_rooms.append(room)
    
    conn.close()
    return json.dumps(available_rooms, ensure_ascii=False)

@tool
def book_meeting_room(appointment_id: str, room_id: str, date: str, start_time: str, end_time: str, attendees_count: int) -> str:
    """
    预定会议室
    
    Args:
        appointment_id (str): 关联的约会ID
        room_id (str): 会议室ID
        date (str): 预定日期 (YYYY-MM-DD格式)
        start_time (str): 开始时间 (HH:MM格式)
        end_time (str): 结束时间 (HH:MM格式)
        attendees_count (int): 参会人数
    
    Returns:
        str: 预定结果的JSON信息
    """
    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()
    
    # 检查会议室是否可用
    # 获取会议室的位置信息
    cursor.execute("SELECT location FROM meeting_rooms WHERE room_id = ?", (room_id,))
    room_location = cursor.fetchone()
    location = room_location[0] if room_location else ""
    
    available_rooms = json.loads(find_available_rooms(date, start_time, end_time, location, attendees_count))
    room_available = any(room['room_id'] == room_id for room in available_rooms)
    
    if not room_available:
        # 获取会议室信息以便检查是否存在
        cursor.execute("SELECT * FROM meeting_rooms WHERE room_id = ?", (room_id,))
        room_exists = cursor.fetchone()
        
        if not room_exists:
            conn.close()
            return json.dumps({"success": False, "message": "会议室不存在"}, ensure_ascii=False)
        else:
            conn.close()
            return json.dumps({"success": False, "message": "该会议室在指定时间不可用"}, ensure_ascii=False)
    
    # 创建预定
    booking_id = f"BOOK-{uuid.uuid4().hex[:12]}"
    cursor.execute(
        "INSERT INTO room_bookings (booking_id, room_id, appointment_id, booking_date, start_time, end_time, attendees_count, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (booking_id, room_id, appointment_id, date, start_time, end_time, attendees_count, "confirmed")
    )
    
    # 获取会议室信息
    cursor.execute("SELECT name, capacity FROM meeting_rooms WHERE room_id = ?", (room_id,))
    room_info = cursor.fetchone()
    
    conn.commit()
    conn.close()
    
    return json.dumps({
        "success": True,
        "booking_id": booking_id,
        "room_id": room_id,
        "room_name": room_info[0],
        "capacity": room_info[1],
        "date": date,
        "time": f"{start_time}-{end_time}"
    }, ensure_ascii=False)

@tool
def list_meeting_rooms(location: str = None) -> str:
    """
    列出所有或指定地点的会议室
    
    Args:
        location (str, optional): 地点筛选，如"北京"或"上海"
    
    Returns:
        str: 会议室列表的JSON格式
    """
    conn = sqlite3.connect("appointments.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if location:
        cursor.execute("SELECT * FROM meeting_rooms WHERE location = ? ORDER BY capacity", (location,))
    else:
        cursor.execute("SELECT * FROM meeting_rooms ORDER BY location, capacity")
        
    rooms = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return json.dumps(rooms, ensure_ascii=False)

@tool
def create_appointment(date: str, title: str, description: str, 
                      meeting_type: str = "online", location: str = None, attendees_count: int = None) -> str:
    """
    创建新的约会或会议。
    
    Args:
        date (str): 约会日期和时间 (格式: YYYY-MM-DD HH:MM).
        title (str): 约会标题.
        description (str): 约会描述.
        meeting_type (str, optional): 会议类型，"online"或"offline"，默认为"online".
        location (str, optional): 约会地点，线下会议必填.
        attendees_count (int, optional): 如果是线下会议，需提供参会人数.
    
    Returns:
        str: 创建结果信息，包含约会ID和会议室预定信息(如果有).
    """
    # 验证日期格式
    try:
        dt = datetime.strptime(date, "%Y-%m-%d %H:%M")
    except ValueError:
        raise ValueError("日期必须为'YYYY-MM-DD HH:MM'格式")
    
    # 生成唯一ID
    appointment_id = str(uuid.uuid4())
    
    # 连接数据库
    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()
    
    # 创建appointments表(如果不存在)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,
        date TEXT,
        location TEXT,
        title TEXT,
        description TEXT,
        meeting_type TEXT DEFAULT 'online'
    )
    """)
    
    # 确保meeting_type的值是小写的，以便统一处理
    if meeting_type:
        meeting_type = meeting_type.lower()
    
    # 插入约会数据
    cursor.execute(
        "INSERT INTO appointments (id, date, location, title, description, meeting_type) VALUES (?, ?, ?, ?, ?, ?)",
        (appointment_id, date, location, title, description, meeting_type)
    )
    
    result = f"约会已创建，ID: {appointment_id}"
    
    # 如果是线下会议，处理会议室预定
    if meeting_type == "offline":
        # 检查是否提供了参会地点
        if location is None:
            conn.commit()
            conn.close()
            return f"{result}，但未提供会议地点，无法预定会议室。请使用update_appointment更新约会并添加会议地点。"
            
        # 检查是否提供了参会人数
        if attendees_count is None:
            conn.commit()
            conn.close()
            return f"{result}，但未提供参会人数，无法预定会议室。请使用update_appointment更新约会并添加参会人数。"
        
        # 从日期中提取日期和时间部分
        booking_date = dt.strftime("%Y-%m-%d")
        start_time = dt.strftime("%H:%M")
        # 默认会议时长为1小时
        end_dt = dt + timedelta(hours=1)
        end_time = end_dt.strftime("%H:%M")
        
        # 检查location是否为有效的会议室地点（北京或上海）
        valid_locations = ["北京", "上海"]
        meeting_location = location
        
        if meeting_location not in valid_locations:
            # 如果约会地点不是有效的会议室地点，默认使用北京
            meeting_location = "北京"
            result += f"（注意：已将会议室地点从\"{location}\"更改为\"{meeting_location}\"）"
        
        try:
            # 查找可用会议室
            available_rooms_json = find_available_rooms(booking_date, start_time, end_time, meeting_location, attendees_count)
            available_rooms = json.loads(available_rooms_json)
            
            if available_rooms:
                # 选择第一个可用的会议室
                room = available_rooms[0]
                
                try:
                    # 创建会议室预定
                    booking_result = json.loads(book_meeting_room(appointment_id, room['room_id'], booking_date, start_time, end_time, attendees_count))
                    if booking_result.get('success', False):
                        result += f"，已预定会议室：{room['name']}（容量：{room['capacity']}人），预定ID: {booking_result['booking_id']}"
                    else:
                        result += f"，但会议室预定失败：{booking_result.get('message', '未知错误')}"
                except Exception as e:
                    result += f"，但会议室预定过程中发生错误：{str(e)}"
            else:
                # 处理无可用会议室的情况
                alternatives = handle_no_rooms_available(booking_date, start_time, end_time, meeting_location, attendees_count)
                alt_msg = f"，但{meeting_location}当前无可用会议室。\n"
                
                if alternatives['alternative_times']:
                    alt_times = ", ".join([f"{t['start']}-{t['end']}" for t in alternatives['alternative_times'][:3]])
                    alt_msg += f"可选时间: {alt_times}\n"
                    
                if alternatives['alternative_locations']:
                    alt_locations = ", ".join([f"{l['location']}({l['count']}间)" for l in alternatives['alternative_locations']])
                    alt_msg += f"可选地点: {alt_locations}\n"
                
                result += alt_msg
        except Exception as e:
            result += f"，但查找会议室时发生错误：{str(e)}"
    
    conn.commit()
    conn.close()
    return result

@tool
def list_appointments() -> str:
    """
    列出所有约会和会议信息，包括会议室预定详情
    
    Returns:
        str: 可用的约会列表 
    """
    # 检查数据库是否存在
    if not os.path.exists('appointments.db'):
        return "没有可用的约会"
    
    conn = sqlite3.connect('appointments.db')
    conn.row_factory = sqlite3.Row  # 启用按名称访问列
    cursor = conn.cursor()
    
    # 检查appointments表是否存在
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
        if not cursor.fetchone():
            conn.close()
            return "没有可用的约会"
        
        cursor.execute("SELECT * FROM appointments ORDER BY date")
        rows = cursor.fetchall()
        
        # 转换为字典列表
        appointments = []
        for row in rows:
            # 检查该行是否有meeting_type列
            try:
                meeting_type = row['meeting_type']
            except:
                meeting_type = "online"  # 如果没有此列，默认为online
                
            appointment = {
                'id': row['id'],
                'date': row['date'],
                'location': row['location'],
                'title': row['title'],
                'description': row['description'],
                'meeting_type': meeting_type
            }
            
            # 如果是线下会议，查找相关的会议室预定
            if meeting_type == "offline":
                try:
                    cursor.execute("""
                    SELECT rb.booking_id, rb.attendees_count, rb.start_time, rb.end_time, 
                           mr.name as room_name, mr.capacity 
                    FROM room_bookings rb 
                    JOIN meeting_rooms mr ON rb.room_id = mr.room_id
                    WHERE rb.appointment_id = ?
                    """, (row['id'],))
                    
                    room_booking = cursor.fetchone()
                    if room_booking:
                        appointment['room_booking'] = {
                            'booking_id': room_booking['booking_id'],
                            'room_name': room_booking['room_name'],
                            'capacity': room_booking['capacity'],
                            'attendees_count': room_booking['attendees_count'],
                            'time': f"{room_booking['start_time']}-{room_booking['end_time']}"
                        }
                except:
                    # 如果会议室表不存在，继续而不添加会议室信息
                    pass
            
            appointments.append(appointment)
        
        conn.close()
        return str(appointments)
    
    except sqlite3.Error as e:
        conn.close()
        return f"错误: {str(e)}"

@tool
def cancel_appointment(appointment_id: str) -> str:
    """
    取消约会和关联的会议室预定
    
    Args:
        appointment_id (str): 要取消的约会ID
    
    Returns:
        str: 取消操作的结果
    """
    # 检查数据库是否存在
    if not os.path.exists('appointments.db'):
        return f"约会 {appointment_id} 不存在"
    
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    
    # 检查约会是否存在
    cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
    appointment = cursor.fetchone()
    
    if not appointment:
        conn.close()
        return f"约会 {appointment_id} 不存在"
    
    # 获取约会相关信息（用于返回消息）
    appointment_info = {}
    if appointment:
        columns = [col[0] for col in cursor.description]
        for i, col in enumerate(columns):
            appointment_info[col] = appointment[i]
    
    # 检查是否有关联的会议室预定
    cursor.execute("SELECT rb.booking_id, mr.name as room_name FROM room_bookings rb JOIN meeting_rooms mr ON rb.room_id = mr.room_id WHERE rb.appointment_id = ?", (appointment_id,))
    booking = cursor.fetchone()
    
    result = f"约会 \"{appointment_info.get('title', '无标题')}\"（ID: {appointment_id}）已取消"
    
    # 如果有会议室预定，删除预定
    if booking:
        booking_id = booking[0]
        room_name = booking[1]
        cursor.execute("DELETE FROM room_bookings WHERE booking_id = ?", (booking_id,))
        result += f"，关联的会议室预定 {room_name}（预定ID: {booking_id}）也已取消"
    
    # 删除约会
    cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
    
    conn.commit()
    conn.close()
    return result

@tool
def update_appointment(appointment_id: str, date: str = None, location: str = None, 
                      title: str = None, description: str = None,
                      meeting_type: str = None, attendees_count: int = None) -> str:
    """
    更新已有约会信息，包括会议类型和参会人数
    
    Args:
        appointment_id (str): 约会ID
        date (str, optional): 约会日期时间 (YYYY-MM-DD HH:MM格式)
        location (str, optional): 约会地点
        title (str, optional): 约会标题
        description (str, optional): 约会描述
        meeting_type (str, optional): 会议类型 ("online"或"offline")
        attendees_count (int, optional): 如果是线下会议，参会人数
        
    Returns:
        str: 更新结果
    """
    # 检查数据库是否存在
    if not os.path.exists('appointments.db'):
        return f"约会 {appointment_id} 不存在"
    
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    
    # 检查约会是否存在
    cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
    appointment = cursor.fetchone()
    
    if not appointment:
        conn.close()
        return f"约会 {appointment_id} 不存在"
    
    # 验证日期格式
    if date:
        try:
            dt = datetime.strptime(date, '%Y-%m-%d %H:%M')
        except ValueError:
            conn.close()
            return "日期必须为'YYYY-MM-DD HH:MM'格式"
    else:
        # 如果没有提供日期，从数据库获取现有日期用于会议室预订
        cursor.execute("SELECT date FROM appointments WHERE id = ?", (appointment_id,))
        date_row = cursor.fetchone()
        if date_row:
            date = date_row[0]
            dt = datetime.strptime(date, '%Y-%m-%d %H:%M')
    
    # 构建更新查询
    update_fields = []
    params = []
    
    if date:
        update_fields.append("date = ?")
        params.append(date)
    
    if location:
        update_fields.append("location = ?")
        params.append(location)
    else:
        # 获取当前位置用于会议室预定
        cursor.execute("SELECT location FROM appointments WHERE id = ?", (appointment_id,))
        loc_row = cursor.fetchone()
        if loc_row:
            location = loc_row[0]
    
    if title:
        update_fields.append("title = ?")
        params.append(title)
    
    if description:
        update_fields.append("description = ?")
        params.append(description)
    
    if meeting_type:
        update_fields.append("meeting_type = ?")
        params.append(meeting_type)
    else:
        # 获取当前会议类型
        cursor.execute("SELECT meeting_type FROM appointments WHERE id = ?", (appointment_id,))
        try:
            mt_row = cursor.fetchone()
            if mt_row:
                meeting_type = mt_row[0]
        except:
            # 如果meeting_type字段不存在，默认为online
            meeting_type = "online"
    
    # 如果没有字段需要更新
    if not update_fields and attendees_count is None:
        conn.close()
        return "没有需要更新的内容"
    
    result = ""
    
    # 更新约会信息
    if update_fields:
        query = f"UPDATE appointments SET {', '.join(update_fields)} WHERE id = ?"
        params.append(appointment_id)
        
        cursor.execute(query, params)
        result = f"约会 {appointment_id} 已更新"
    
    # 处理会议室预定更新
    if meeting_type == "offline" or attendees_count is not None:
        # 从日期中提取日期和时间部分
        booking_date = dt.strftime("%Y-%m-%d")
        start_time = dt.strftime("%H:%M")
        end_time = (dt + timedelta(hours=1)).strftime("%H:%M")
        
        # 检查是否已有会议室预定
        cursor.execute("SELECT * FROM room_bookings WHERE appointment_id = ?", (appointment_id,))
        existing_booking = cursor.fetchone()
        
        if existing_booking:
            # 如果参会人数有变化，检查当前会议室是否还适合
            if attendees_count is not None:
                cursor.execute("SELECT room_id FROM room_bookings WHERE appointment_id = ?", (appointment_id,))
                room_id = cursor.fetchone()[0]
                
                cursor.execute("SELECT capacity FROM meeting_rooms WHERE room_id = ?", (room_id,))
                current_capacity = cursor.fetchone()[0]
                
                if attendees_count > current_capacity:
                    # 需要找更大的会议室
                    avail_rooms = json.loads(find_available_rooms(booking_date, start_time, end_time, location, attendees_count))
                    
                    if avail_rooms:
                        # 取消原预定
                        cursor.execute("DELETE FROM room_bookings WHERE appointment_id = ?", (appointment_id,))
                        
                        # 创建新预定
                        new_room = avail_rooms[0]
                        booking_result = json.loads(book_meeting_room(appointment_id, new_room['room_id'], booking_date, start_time, end_time, attendees_count))
                        
                        if booking_result.get('success', False):
                            result += f"，已更换至容量为{new_room['capacity']}人的会议室：{new_room['name']}"
                        else:
                            result += "，但更换会议室失败"
                    else:
                        result += "，但没有找到容量更大的可用会议室"
                else:
                    # 更新现有预定的参会人数
                    cursor.execute("UPDATE room_bookings SET attendees_count = ? WHERE appointment_id = ?", 
                                 (attendees_count, appointment_id))
                    result += f"，会议室预定人数已更新为{attendees_count}人"
        elif meeting_type == "offline":
            # 没有现有预定，创建新预定
            if attendees_count is None:
                result += "，但未提供参会人数，无法预定会议室"
            else:
                avail_rooms = json.loads(find_available_rooms(booking_date, start_time, end_time, location, attendees_count))
                
                if avail_rooms:
                    room = avail_rooms[0]
                    booking_result = json.loads(book_meeting_room(appointment_id, room['room_id'], booking_date, start_time, end_time, attendees_count))
                    
                    if booking_result.get('success', False):
                        result += f"，已预定会议室：{room['name']}（容量：{room['capacity']}人）"
                    else:
                        result += "，但会议室预定失败"
                else:
                    result += "，但没有找到可用的会议室"
        elif meeting_type == "online" and existing_booking:
            # 如果从线下会议改为线上会议，取消会议室预定
            cursor.execute("DELETE FROM room_bookings WHERE appointment_id = ?", (appointment_id,))
            result += "，已取消会议室预定"
    
    conn.commit()
    conn.close()
    
    return result
