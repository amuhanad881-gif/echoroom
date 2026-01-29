#!/usr/bin/env python3
"""
EchoRoom - Secure Voice & Text Chat with Gmail Validation
FIXED VERSION - No Syntax Errors
"""

import uuid
import hashlib
import json
import os
import smtplib
import ssl
import re
import secrets
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room, leave_room

# Initialize Flask app FIRST
app = Flask(__name__)
app.secret_key = 'echo-room-secret-key-2025'

# Initialize SocketIO AFTER app
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='threading')

# Email Configuration (REPLACE WITH REAL CREDENTIALS)
EMAIL_SENDER = "echoroomteam1@gmail.com"  # Replace with real Gmail
EMAIL_PASSWORD = "jxsb vfkm zseq zwqq"  # Replace with Gmail App Password
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587

# Email validation regex
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'

# Session token expiry (30 days)
SESSION_EXPIRY_DAYS = 30

# إضافة encoder مخصص للتاريخ
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def is_valid_gmail(email):
    """Check if email is a valid Gmail address"""
    return re.match(EMAIL_REGEX, email) is not None

def send_welcome_email(to_email, username, verification_token=None):
    """Send welcome email to new users"""
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Welcome to EchoRoom!"
        msg["From"] = EMAIL_SENDER
        msg["To"] = to_email
        
        # HTML Email Content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #00e5ff, #00b8d4); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1>🎤 EchoRoom</h1>
                    <p>Your new space for real-time communication</p>
                </div>
                <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p>Hi {username} 👋,</p>
                    
                    <p>Welcome to <strong>EchoRoom</strong> — your new space for real-time voice and chat communication.</p>
                    
                    <p>At EchoRoom, you can:</p>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin: 10px 0; padding-left: 25px; position: relative;">✅ 🎙️ Join voice rooms and talk instantly with friends</li>
                        <li style="margin: 10px 0; padding-left: 25px; position: relative;">✅ 💬 Chat in servers built around your interests</li>
                        <li style="margin: 10px 0; padding-left: 25px; position: relative;">✅ 🌍 Create your own rooms and connect with people anywhere</li>
                        <li style="margin: 10px 0; padding-left: 25px; position: relative;">✅ 🚀 Enjoy smooth, simple, and reliable communication</li>
                    </ul>
                    
                    <p>We're excited to have you with us and can't wait to see the communities you'll build.</p>
                    
                    <p>If you have any questions or feedback, we're always listening.</p>
                    
                    <p>See you inside EchoRoom,<br>
                    <strong>The EchoRoom Team</strong></p>
                    
                    <div style="text-align: center; margin-top: 30px; color: #666; font-size: 12px;">
                        <p>This is an automated message, please do not reply to this email.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""Hi {username} 👋,

Welcome to **EchoRoom** — your new space for real-time voice and chat communication.

At EchoRoom, you can:
🎙️ Join voice rooms and talk instantly with friends
💬 Chat in servers built around your interests
🌍 Create your own rooms and connect with people anywhere
🚀 Enjoy smooth, simple, and reliable communication

We're excited to have you with us and can't wait to see the communities you'll build.

If you have any questions or feedback, we're always listening.

See you inside EchoRoom,
**The EchoRoom Team**"""
        
        # Attach both versions
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)
        
        # Create secure SSL context
        context = ssl.create_default_context()
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        
        print(f"📧 Welcome email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def generate_session_token():
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

def hash_password(password, salt=None):
    """Hash password with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    return hashlib.sha256((password + salt).encode()).hexdigest(), salt

def verify_password(password, hashed_password, salt):
    """Verify password against stored hash"""
    return hashlib.sha256((password + salt).encode()).hexdigest() == hashed_password

# ==================== HTML TEMPLATE WITH AUTO-LOGIN ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎤 EchoRoom - Voice & Text Chat</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        /* ALL YOUR ORIGINAL CSS STAYS THE SAME */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            color: #fff; min-height: 100vh;
        }
        .container { 
            display: flex; height: 100vh; max-width: 1600px; 
            margin: 0 auto; box-shadow: 0 0 50px rgba(0,0,0,0.5);
        }
        .sidebar { 
            width: 280px; background: rgba(20, 20, 30, 0.95); 
            padding: 20px; overflow-y: auto; 
            border-right: 1px solid rgba(255,255,255,0.1);
        }
        .logo { 
            font-size: 24px; font-weight: bold; margin-bottom: 30px; 
            color: #00e5ff; display: flex; align-items: center; 
            gap: 10px; padding: 10px; 
            background: rgba(0, 229, 255, 0.1); border-radius: 10px;
        }
        .logo i { animation: pulse 2s infinite; }
        .nav-section { margin-bottom: 25px; }
        .nav-section h3 { 
            font-size: 12px; text-transform: uppercase; 
            letter-spacing: 1px; color: #888; margin-bottom: 10px; 
            padding-left: 10px;
        }
        .nav-item { 
            padding: 12px 15px; margin: 5px 0; 
            background: rgba(255,255,255,0.05); border-radius: 8px; 
            cursor: pointer; transition: all 0.3s; 
            display: flex; align-items: center; gap: 12px;
        }
        .nav-item:hover { 
            background: rgba(0, 229, 255, 0.2); 
            transform: translateX(5px);
        }
        .nav-item.active { 
            background: rgba(0, 229, 255, 0.3); 
            border-left: 3px solid #00e5ff;
        }
        .badge { 
            background: #ff2e63; color: white; padding: 2px 8px; 
            border-radius: 10px; font-size: 11px; margin-left: auto;
        }
        .user-profile { 
            margin-top: auto; padding: 15px; 
            background: rgba(0,0,0,0.2); border-radius: 15px; 
            display: flex; align-items: center; gap: 15px; 
            cursor: pointer; transition: all 0.3s;
        }
        .user-profile:hover { 
            background: rgba(0, 229, 255, 0.1); 
            transform: translateY(-2px);
        }
        .user-avatar { 
            width: 50px; height: 50px; border-radius: 50%; 
            overflow: hidden; border: 3px solid #00e5ff; 
            background: rgba(255,255,255,0.1); 
            display: flex; align-items: center; 
            justify-content: center; font-size: 24px;
        }
        .user-avatar img { width: 100%; height: 100%; object-fit: cover; }
        .user-info { flex: 1; }
        .user-info strong { display: block; font-size: 16px; margin-bottom: 5px; }
        .user-info .status { font-size: 12px; opacity: 0.7; }
        .premium-badge { 
            background: linear-gradient(45deg, #ffd700, #ffed4e); 
            color: #333; padding: 2px 8px; border-radius: 10px; 
            font-size: 10px; font-weight: bold; margin-top: 5px; 
            display: inline-block;
        }
        .upgrade-btn { 
            padding: 8px 16px; 
            background: linear-gradient(135deg, #ffd700, #ffed4e); 
            color: #333; border: none; border-radius: 10px; 
            cursor: pointer; font-size: 12px; font-weight: bold; 
            transition: all 0.3s;
        }
        .upgrade-btn:hover { 
            transform: scale(1.05); 
            box-shadow: 0 5px 15px rgba(255,215,0,0.3);
        }
        .main { 
            flex: 1; display: flex; flex-direction: column; 
            background: rgba(25, 25, 35, 0.95); position: relative;
        }
        .chat-header { 
            padding: 20px; background: rgba(0,0,0,0.3); 
            border-bottom: 1px solid rgba(255,255,255,0.1); 
            display: flex; justify-content: space-between; 
            align-items: center; backdrop-filter: blur(10px);
        }
        .chat-header h2 { 
            display: flex; align-items: center; gap: 10px; 
            color: #00e5ff;
        }
        .chat-messages { 
            flex: 1; padding: 20px; overflow-y: auto; 
            display: flex; flex-direction: column; gap: 15px; 
            background: rgba(15, 15, 25, 0.8);
        }
        .message { 
            display: flex; gap: 15px; 
            animation: slideIn 0.3s ease;
        }
        .message.own { flex-direction: row-reverse; }
        .message-avatar { 
            width: 40px; height: 40px; border-radius: 50%; 
            overflow: hidden; border: 2px solid rgba(255,255,255,0.1); 
            flex-shrink: 0; background: rgba(255,255,255,0.1); 
            display: flex; align-items: center; 
            justify-content: center; font-size: 18px;
        }
        .message-avatar img { width: 100%; height: 100%; object-fit: cover; }
        .message-content { flex: 1; max-width: 70%; }
        .message-bubble { 
            background: rgba(255,255,255,0.07); padding: 15px; 
            border-radius: 15px; border: 1px solid rgba(255,255,255,0.05);
        }
        .message.own .message-bubble { 
            background: rgba(0, 229, 255, 0.2); 
            border-color: rgba(0, 229, 255, 0.3);
        }
        .message-header { 
            display: flex; justify-content: space-between; 
            margin-bottom: 8px; font-size: 12px; opacity: 0.8;
        }
        .message-text { line-height: 1.6; font-size: 15px; }
        .modal { 
            display: none; position: fixed; top: 0; left: 0; 
            width: 100%; height: 100%; 
            background: rgba(0,0,0,0.95); z-index: 3000; 
            justify-content: center; align-items: center; 
            backdrop-filter: blur(10px);
        }
        .settings-modal-content { 
            background: linear-gradient(135deg, rgba(30,30,40,0.98), rgba(20,20,30,0.98)); 
            padding: 40px; border-radius: 20px; width: 90%; 
            max-width: 800px; max-height: 90vh; overflow-y: auto; 
            border: 1px solid rgba(0,229,255,0.3); 
            box-shadow: 0 0 50px rgba(0,229,255,0.2); position: relative;
        }
        .close-btn { 
            position: absolute; top: 20px; right: 20px; 
            background: transparent; border: none; 
            color: rgba(255,255,255,0.7); font-size: 24px; 
            cursor: pointer; transition: all 0.3s; width: 40px; 
            height: 40px; border-radius: 50%; 
            display: flex; align-items: center; justify-content: center;
        }
        .close-btn:hover { 
            background: rgba(255,255,255,0.1); color: #00e5ff; 
            transform: rotate(90deg);
        }
        .settings-tabs { 
            display: flex; gap: 10px; margin-bottom: 30px; 
            border-bottom: 1px solid rgba(255,255,255,0.1); 
            padding-bottom: 10px;
        }
        .settings-tab { 
            padding: 12px 24px; background: transparent; border: none; 
            color: rgba(255,255,255,0.7); cursor: pointer; 
            font-size: 16px; border-radius: 10px; transition: all 0.3s;
        }
        .settings-tab:hover { background: rgba(255,255,255,0.05); }
        .settings-tab.active { 
            background: rgba(0, 229, 255, 0.2); color: #00e5ff; 
            border-bottom: 2px solid #00e5ff;
        }
        .settings-section { display: none; animation: fadeIn 0.5s ease; }
        .settings-section.active { display: block; }
        .avatar-preview-container { text-align: center; margin-bottom: 30px; }
        .avatar-preview { 
            width: 150px; height: 150px; border-radius: 50%; 
            overflow: hidden; margin: 0 auto 20px; 
            border: 4px solid #00e5ff; background: rgba(255,255,255,0.1); 
            position: relative;
        }
        .avatar-preview img { width: 100%; height: 100%; object-fit: cover; }
        .avatar-placeholder { 
            display: flex; align-items: center; justify-content: center; 
            width: 100%; height: 100%; font-size: 48px; 
            color: rgba(255,255,255,0.5);
        }
        .avatar-overlay { 
            position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
            background: rgba(0,0,0,0.7); display: flex; align-items: center; 
            justify-content: center; opacity: 0; transition: opacity 0.3s; 
            cursor: pointer;
        }
        .avatar-preview:hover .avatar-overlay { opacity: 1; }
        .banner-preview-container { margin-bottom: 30px; }
        .banner-preview { 
            width: 100%; height: 200px; border-radius: 15px; 
            overflow: hidden; margin-bottom: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            position: relative;
        }
        .banner-placeholder { 
            display: flex; align-items: center; justify-content: center; 
            width: 100%; height: 100%; font-size: 48px; 
            color: rgba(255,255,255,0.3);
        }
        .file-input-wrapper { position: relative; margin-bottom: 20px; }
        .file-input { 
            position: absolute; width: 0; height: 0; opacity: 0;
        }
        .file-input-label { 
            display: block; padding: 15px; 
            background: rgba(0, 229, 255, 0.1); 
            border: 2px dashed rgba(0, 229, 255, 0.5); 
            border-radius: 10px; text-align: center; cursor: pointer; 
            transition: all 0.3s;
        }
        .file-input-label:hover { 
            background: rgba(0, 229, 255, 0.2); 
            border-color: #00e5ff;
        }
        .form-group { margin-bottom: 25px; }
        .form-group label { 
            display: block; margin-bottom: 10px; 
            color: rgba(255,255,255,0.9); font-size: 14px; 
            font-weight: 500;
        }
        .form-group input, .form-group select, .form-group textarea { 
            width: 100%; padding: 15px; 
            border: 1px solid rgba(255,255,255,0.2); 
            border-radius: 10px; background: rgba(255,255,255,0.08); 
            color: white; font-size: 16px; transition: all 0.3s;
        }
        .btn { 
            padding: 15px 30px; 
            background: linear-gradient(135deg, #00e5ff, #00b8d4); 
            color: white; border: none; border-radius: 10px; 
            cursor: pointer; font-size: 16px; font-weight: bold; 
            transition: all 0.3s; width: 100%;
        }
        .btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 10px 20px rgba(0,229,255,0.3);
        }
        .btn-success { 
            background: linear-gradient(135deg, #43b581, #3ca374);
        }
        .btn-danger { 
            background: linear-gradient(135deg, #ff2e63, #d81b60);
        }
        .btn-premium { 
            background: linear-gradient(135deg, #ffd700, #ffed4e); 
            color: #333;
        }
        .premium-feature-badge { 
            background: linear-gradient(45deg, #ffd700, #ffed4e); 
            color: #333; padding: 4px 12px; border-radius: 10px; 
            font-size: 12px; font-weight: bold; margin-left: 10px;
        }
        .message-input-area { 
            padding: 20px; background: rgba(0,0,0,0.3); 
            border-top: 1px solid rgba(255,255,255,0.1); 
            display: flex; gap: 10px; align-items: center; 
            position: relative;
        }
        .message-input { 
            flex: 1; padding: 15px 20px; border: none; 
            border-radius: 25px; background: rgba(255,255,255,0.08); 
            color: white; font-size: 16px; outline: none;
        }
        .input-btn { 
            width: 50px; height: 50px; border-radius: 50%; border: none; 
            background: #00e5ff; color: white; cursor: pointer; 
            font-size: 18px; transition: all 0.3s; 
            display: flex; align-items: center; justify-content: center;
        }
        .input-btn:hover { 
            background: #00b8d4; transform: scale(1.1);
        }
        @keyframes slideIn { 
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeIn { 
            from { opacity: 0; } to { opacity: 1; }
        }
        @keyframes pulse { 
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .notification { 
            position: fixed; top: 20px; right: 20px; 
            padding: 15px 25px; background: rgba(30,30,40,0.95); 
            border-radius: 10px; border-left: 4px solid #00e5ff; 
            animation: slideIn 0.3s ease; z-index: 3000; 
            backdrop-filter: blur(10px); 
            border: 1px solid rgba(255,255,255,0.1);
        }
        .notification.success { border-left-color: #43b581; }
        .notification.error { border-left-color: #ff2e63; }
        #auth-modal { display: flex; }
        .auth-modal-content { 
            background: linear-gradient(135deg, rgba(30,30,40,0.95), rgba(20,20,30,0.95)); 
            padding: 40px; border-radius: 20px; width: 90%; 
            max-width: 400px; border: 1px solid rgba(0,229,255,0.3); 
            box-shadow: 0 0 50px rgba(0,229,255,0.2); position: relative;
        }
        .auth-tabs { display: flex; gap: 10px; margin-bottom: 30px; }
        .auth-tab { 
            flex: 1; padding: 12px; background: transparent; 
            border: none; color: rgba(255,255,255,0.7); 
            cursor: pointer; font-size: 16px; border-radius: 10px; 
            transition: all 0.3s;
        }
        .auth-tab:hover { background: rgba(255,255,255,0.05); }
        .auth-tab.active { 
            background: rgba(0, 229, 255, 0.2); color: #00e5ff;
        }
        .auth-section { display: none; }
        .auth-section.active { display: block; }
        
        /* NEW: Gmail validation message */
        .email-hint {
            font-size: 12px;
            opacity: 0.7;
            margin-top: 5px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .email-hint.valid {
            color: #43b581;
        }
        .email-hint.invalid {
            color: #ff2e63;
        }
        
        /* NEW: Auto-login checkbox */
        .remember-me {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 15px 0;
        }
        .remember-me input[type="checkbox"] {
            width: 18px;
            height: 18px;
        }
        
        /* NEW BUTTONS FOR FEATURES */
        .action-btn {
            padding: 8px 15px;
            background: rgba(0, 229, 255, 0.1);
            border: 1px solid rgba(0, 229, 255, 0.3);
            border-radius: 8px;
            color: white;
            cursor: pointer;
            font-size: 14px;
            margin: 5px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .action-btn:hover {
            background: rgba(0, 229, 255, 0.2);
        }
        .action-btn.delete {
            background: rgba(255, 46, 99, 0.1);
            border-color: rgba(255, 46, 99, 0.3);
        }
        .action-btn.delete:hover {
            background: rgba(255, 46, 99, 0.2);
        }
        .action-btn.call {
            background: rgba(67, 181, 129, 0.1);
            border-color: rgba(67, 181, 129, 0.3);
        }
        .action-btn.call:hover {
            background: rgba(67, 181, 129, 0.2);
        }
        .room-header-actions {
            display: flex;
            gap: 10px;
            margin-left: 20px;
        }
        .friend-status {
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 10px;
            background: rgba(67, 181, 129, 0.2);
            color: #43b581;
            margin-left: auto;
        }
        .friend-status.offline {
            background: rgba(255,255,255,0.1);
            color: #888;
        }
        .message-actions {
            opacity: 0;
            transition: opacity 0.3s;
            display: flex;
            gap: 5px;
            position: absolute;
            right: 10px;
            top: 10px;
        }
        .message:hover .message-actions {
            opacity: 1;
        }
        .msg-action-btn {
            background: rgba(0,0,0,0.5);
            border: none;
            color: white;
            width: 25px;
            height: 25px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 11px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .msg-action-btn:hover {
            background: #00e5ff;
        }
        .invite-link-box {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            word-break: break-all;
            font-family: monospace;
        }
        .room-type-badge {
            font-size: 10px;
            padding: 2px 8px;
            border-radius: 10px;
            background: rgba(0, 229, 255, 0.2);
            color: #00e5ff;
            margin-left: 10px;
        }
        .room-type-badge.private {
            background: rgba(255, 215, 0, 0.2);
            color: #ffd700;
        }
        .room-type-badge.voice {
            background: rgba(255, 46, 99, 0.2);
            color: #ff2e63;
        }
        .room-type-badge.dm {
            background: rgba(67, 181, 129, 0.2);
            color: #43b581;
        }
        
        /* NEW: Friend chat buttons */
        .friend-chat-btn {
            background: transparent;
            border: none;
            color: #00e5ff;
            cursor: pointer;
            font-size: 14px;
            margin-left: 5px;
            padding: 2px 8px;
            border-radius: 5px;
            transition: all 0.3s;
        }
        .friend-chat-btn:hover {
            background: rgba(0, 229, 255, 0.1);
        }
        
        /* NEW: Add friend to room modal */
        .friend-room-select {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            color: white;
        }
/* Voice Message Styles */
        .voice-recording-indicator {
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 46, 99, 0.95);
            color: white;
            padding: 15px 30px;
            border-radius: 25px;
            display: none;
            align-items: center;
            gap: 10px;
            z-index: 2000;
            animation: pulse 1.5s infinite;
            box-shadow: 0 5px 20px rgba(255, 46, 99, 0.5);
        }

        .voice-recording-indicator.active {
            display: flex;
        }

        .recording-dot {
            width: 12px;
            height: 12px;
            background: white;
            border-radius: 50%;
            animation: blink 1s infinite;
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        .voice-message {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 15px;
            background: rgba(0, 229, 255, 0.1);
            border-radius: 20px;
            border: 1px solid rgba(0, 229, 255, 0.3);
            width: 100%;
            max-width: 350px;
        }

        .voice-play-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #00e5ff;
            border: none;
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
            flex-shrink: 0;
        }

        .voice-play-btn:hover {
            background: #00b8d4;
            transform: scale(1.1);
        }

        .voice-play-btn.playing {
            background: #ff2e63;
        }

        .voice-waveform {
            flex: 1;
            height: 30px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            position: relative;
            overflow: hidden;
        }

        .voice-progress {
            position: absolute;
            left: 0;
            top: 0;
            height: 100%;
            background: rgba(0, 229, 255, 0.3);
            border-radius: 15px;
            transition: width 0.1s;
        }

        .voice-duration {
            font-size: 12px;
            opacity: 0.7;
            min-width: 40px;
            text-align: right;
        }

        .voice-record-btn {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: rgba(255, 46, 99, 0.2);
            border: 2px solid #ff2e63;
            color: #ff2e63;
            cursor: pointer;
            font-size: 18px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .voice-record-btn:hover {
            background: rgba(255, 46, 99, 0.3);
            transform: scale(1.1);
        }

        .voice-record-btn.recording {
            background: #ff2e63;
            color: white;
            animation: pulse 1.5s infinite;
        }

        .voice-cancel-btn {
            position: fixed;
            bottom: 90px;
            right: 30px;
            background: rgba(255, 46, 99, 0.9);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
            display: none;
            transition: all 0.3s;
            z-index: 2000;
        }

        .voice-cancel-btn.active {
            display: block;
        }

        .voice-cancel-btn:hover {
            background: #ff2e63;
            transform: scale(1.05);
        }

    </style>
</head>
<body>
    <!-- Login/Signup Modal -->
    <div class="modal" id="auth-modal">
        <div class="auth-modal-content">
            <button class="close-btn" onclick="hideAuthModal()">
                <i class="fas fa-times"></i>
            </button>
            <div class="auth-header">
                <h2><i class="fas fa-broadcast-tower"></i> EchoRoom</h2>
                <p>Voice & Text Chat Platform</p>
            </div>
            
            <div class="auth-tabs">
                <button class="auth-tab active" onclick="showAuthTab('login', event)">Login</button>
                <button class="auth-tab" onclick="showAuthTab('signup', event)">Sign Up</button>
            </div>
            
            <div id="login-section" class="auth-section active">
                <div class="form-group">
                    <label>Email (Gmail required)</label>
                    <input type="email" id="login-email" placeholder="your@gmail.com" 
                           oninput="validateEmail(this, 'login-email-hint')">
                    <div class="email-hint" id="login-email-hint">
                        <i class="fas fa-info-circle"></i> Must be a valid Gmail address
                    </div>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="login-password" placeholder="••••••••">
                </div>
                <div class="remember-me">
                    <input type="checkbox" id="remember-me" checked>
                    <label for="remember-me">Remember me (Auto-login)</label>
                </div>
                <button class="btn" onclick="login()">
                    <i class="fas fa-sign-in-alt"></i> Login
                </button>
            </div>
            
            <div id="signup-section" class="auth-section">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="signup-username" placeholder="Choose username" 
                           oninput="validateUsername(this)">
                    <div class="email-hint" id="username-hint">
                        <i class="fas fa-info-circle"></i> 3-20 characters, letters and numbers only
                    </div>
                </div>
                <div class="form-group">
                    <label>Email (Real Gmail required)</label>
                    <input type="email" id="signup-email" placeholder="your@gmail.com" 
                           oninput="validateEmail(this, 'signup-email-hint')">
                    <div class="email-hint" id="signup-email-hint">
                        <i class="fas fa-info-circle"></i> Must be a valid Gmail address (@gmail.com)
                    </div>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="signup-password" placeholder="••••••••" 
                           oninput="validatePassword(this)">
                    <div class="email-hint" id="password-hint">
                        <i class="fas fa-info-circle"></i> Minimum 8 characters
                    </div>
                </div>
                <div class="form-group">
                    <label>Confirm Password</label>
                    <input type="password" id="signup-password-confirm" placeholder="••••••••" 
                           oninput="validatePasswordConfirm(this)">
                </div>
                <div class="remember-me">
                    <input type="checkbox" id="remember-signup" checked>
                    <label for="remember-signup">Remember me (Auto-login)</label>
                </div>
                <button class="btn btn-success" onclick="signup()">
                    <i class="fas fa-user-plus"></i> Create Account
                </button>
                <div style="margin-top: 15px; text-align: center; opacity: 0.7; font-size: 12px;">
                    <i class="fas fa-envelope"></i> Welcome email will be sent to your Gmail
                </div>
            </div>
        </div>
    </div>

    <!-- Main App -->
    <div class="container" id="main-app" style="display: none;">
        <!-- Left Sidebar -->
        <div class="sidebar">
            <div class="logo">
                <i class="fas fa-broadcast-tower"></i>
                EchoRoom 🎤
            </div>
            
            <div class="nav-section">
                <h3>Rooms</h3>
                <div id="servers-list"></div>
                <div class="nav-item" onclick="showCreateRoomModal()">
                    <i class="fas fa-plus"></i>
                    <span>Create Room</span>
                </div>
            </div>

            <div class="nav-section">
                <h3>Friends</h3>
                <div id="friends-list" class="friends-list"></div>
                <div class="nav-item" onclick="showAddFriendModal()">
                    <i class="fas fa-user-plus"></i>
                    <span>Add Friend</span>
                </div>
                <div class="nav-item" onclick="showFriendRequestsModal()">
                    <i class="fas fa-user-clock"></i>
                    <span>Friend Requests</span>
                    <span class="badge" id="friend-requests-badge" style="display: none;">0</span>
                </div>
            </div>

            <div class="user-profile" onclick="showSettingsModal()" id="user-profile">
                <div class="user-avatar" id="user-avatar-preview">
                    <div class="avatar-placeholder">
                        <i class="fas fa-user"></i>
                    </div>
                </div>
                <div class="user-info">
                    <strong id="username-display">Guest</strong>
                    <div class="status" id="user-status">Free User</div>
                    <div class="premium-badge" id="premium-badge" style="display: none;">PREMIUM</div>
                </div>
                <button class="upgrade-btn" id="upgrade-btn" onclick="event.stopPropagation(); showUpgradeModal()">
                    <i class="fas fa-crown"></i> Upgrade
                </button>
                <button class="upgrade-btn" id="logout-btn" onclick="event.stopPropagation(); logout()" style="margin-left: 10px; background: rgba(255, 46, 99, 0.2); color: #ff2e63;">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </button>
            </div>
        </div>

        <!-- Main Chat Area -->
        <div class="main">
            <div class="chat-header">
                <h2 id="current-chat-name">
                    <i class="fas fa-hashtag"></i> General
                </h2>
                <div class="room-header-actions" id="room-header-actions" style="display: none;">
                    <button class="action-btn" onclick="showInviteModal()" id="invite-btn">
                        <i class="fas fa-link"></i> Invite
                    </button>
                    <button class="action-btn" onclick="showAddFriendToRoomModal()" id="add-friend-to-room-btn">
                        <i class="fas fa-user-plus"></i> Add Friend
                    </button>
                    <button class="action-btn" onclick="leaveRoom()" id="leave-room-btn">
                        <i class="fas fa-sign-out-alt"></i> Leave
                    </button>
                    <button class="action-btn delete" onclick="deleteRoom()" id="delete-room-btn" style="display: none;">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                    <button class="action-btn call" onclick="toggleCall()" id="call-btn" style="display: none;">
                        <i class="fas fa-phone"></i> Call
                    </button>
                </div>
                <div class="user-info">
                    <div id="connection-status" class="premium-badge">
                        <i class="fas fa-wifi"></i> Connected
                    </div>
                </div>
            </div>

            <div class="chat-messages" id="chat-messages"></div>

            <div class="message-input-area">
                <button class="voice-record-btn" id="voice-record-btn" 
                        onmousedown="startVoiceRecording()" 
                        onmouseup="stopVoiceRecording()"
                        ontouchstart="startVoiceRecording()" 
                        ontouchend="stopVoiceRecording()"
                        title="Hold to record voice message">
                    <i class="fas fa-microphone"></i>
                </button>
                
                <input type="text" class="message-input" id="message-input" 
                       placeholder="Type your message here..." 
                       onkeypress="if(event.keyCode===13) sendMessage()">
                       
                <button class="input-btn" onclick="sendMessage()">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>

            <!-- Voice Recording Indicator -->
            <div class="voice-recording-indicator" id="voice-recording-indicator">
                <div class="recording-dot"></div>
                <span id="recording-timer">0:00</span>
                <span>Recording...</span>
            </div>

            <!-- Voice Cancel Button -->
            <button class="voice-cancel-btn" id="voice-cancel-btn" onclick="cancelVoiceRecording()">
                <i class="fas fa-times"></i> Cancel Recording
            </button>
        </div>

        <!-- Right Panel -->
        <div class="sidebar" style="width: 300px; border-left: 1px solid rgba(255,255,255,0.1); border-right: none;">
            <div class="nav-section">
                <h3>Voice Controls</h3>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <button class="btn" id="mute-btn" onclick="toggleMute()">
                        <i class="fas fa-microphone"></i> Mute
                    </button>
                    <button class="btn" id="deafen-btn" onclick="toggleDeafen()">
                        <i class="fas fa-headset"></i> Deafen
                    </button>
                </div>
            </div>
            
            <div class="nav-section">
                <h3>Room Members</h3>
                <div id="room-members" class="friends-list"></div>
            </div>
        </div>
    </div>

    <!-- Settings Modal -->
    <div class="modal" id="settings-modal">
        <div class="settings-modal-content">
            <button class="close-btn" onclick="hideSettingsModal()">
                <i class="fas fa-times"></i>
            </button>
            
            <div class="settings-header">
                <h2><i class="fas fa-cog"></i> User Settings</h2>
                <p>Customize your EchoRoom profile</p>
            </div>

            <div class="settings-tabs">
                <button class="settings-tab active" onclick="showSettingsTab('profile', event)">
                    <i class="fas fa-user"></i> Profile
                </button>
                <button class="settings-tab" onclick="showSettingsTab('appearance', event)">
                    <i class="fas fa-palette"></i> Appearance
                </button>
                <button class="settings-tab" onclick="showSettingsTab('security', event)">
                    <i class="fas fa-shield-alt"></i> Security
                </button>
            </div>

            <!-- Profile Tab -->
            <div id="profile-tab" class="settings-section active">
                <div class="avatar-preview-container">
                    <div class="avatar-preview" id="settings-avatar-preview">
                        <div class="avatar-placeholder">
                            <i class="fas fa-user"></i>
                        </div>
                        <div class="avatar-overlay" onclick="document.getElementById('avatar-upload').click()">
                            <i class="fas fa-camera"></i> Change Avatar
                        </div>
                    </div>
                    <div class="file-input-wrapper">
                        <input type="file" id="avatar-upload" class="file-input" accept="image/*" onchange="handleAvatarUpload(event)">
                        <label for="avatar-upload" class="file-input-label">
                            <i class="fas fa-upload"></i> Upload Avatar
                        </label>
                    </div>
                </div>

                <div class="banner-preview-container">
                    <h3>Profile Banner <span class="premium-feature-badge">PREMIUM</span></h3>
                    <div class="banner-preview" id="settings-banner-preview">
                        <div class="banner-placeholder">
                            <i class="fas fa-image"></i>
                        </div>
                    </div>
                    <div class="file-input-wrapper">
                        <input type="file" id="banner-upload" class="file-input" accept="image/*" onchange="handleBannerUpload(event)">
                        <label for="banner-upload" class="file-input-label" id="banner-upload-label">
                            <i class="fas fa-upload"></i> Upload Banner
                        </label>
                    </div>
                </div>

                <div class="form-group">
                    <label for="display-name">Display Name</label>
                    <input type="text" id="display-name" placeholder="Enter your display name">
                </div>

                <div class="form-group">
                    <label for="user-bio">Bio</label>
                    <textarea id="user-bio" placeholder="Tell us about yourself..." rows="3"></textarea>
                </div>

                <button class="btn btn-success" onclick="saveProfileSettings()">
                    <i class="fas fa-save"></i> Save Changes
                </button>
            </div>

            <!-- Appearance Tab -->
            <div id="appearance-tab" class="settings-section">
                <div class="form-group">
                    <label>Theme</label>
                    <select id="theme-select">
                        <option value="dark">🌙 Dark Theme</option>
                        <option value="light">☀️ Light Theme</option>
                        <option value="blue">🔵 Blue Theme</option>
                    </select>
                </div>

                <button class="btn btn-success" onclick="saveAppearanceSettings()">
                    <i class="fas fa-save"></i> Save Appearance
                </button>
            </div>

            <!-- Security Tab -->
            <div id="security-tab" class="settings-section">
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" id="security-email" readonly style="background: rgba(255,255,255,0.05);">
                </div>
                
                <div class="form-group">
                    <label>Change Password</label>
                    <input type="password" id="current-password" placeholder="Current password">
                    <input type="password" id="new-password" placeholder="New password" style="margin-top: 10px;">
                    <input type="password" id="confirm-new-password" placeholder="Confirm new password" style="margin-top: 10px;">
                </div>
                
                <button class="btn btn-success" onclick="changePassword()">
                    <i class="fas fa-key"></i> Change Password
                </button>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1);">
                    <button class="btn btn-danger" onclick="logoutAllDevices()">
                        <i class="fas fa-sign-out-alt"></i> Logout All Devices
                    </button>
                    <div style="font-size: 12px; opacity: 0.7; margin-top: 10px;">
                        This will invalidate all active sessions
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Other Modals -->
    <div class="modal" id="create-room-modal">
        <div class="settings-modal-content">
            <button class="close-btn" onclick="hideCreateRoomModal()">
                <i class="fas fa-times"></i>
            </button>
            
            <div class="settings-header">
                <h2><i class="fas fa-plus-circle"></i> Create New Room</h2>
            </div>

            <div class="form-group">
                <label for="room-name">Room Name</label>
                <input type="text" id="room-name" placeholder="Enter room name">
            </div>

            <div class="form-group">
                <label for="room-type">Room Type</label>
                <select id="room-type">
                    <option value="public">Public Room</option>
                    <option value="private">Private Room (Friends Only)</option>
                    <option value="voice">Voice Room</option>
                    <option value="chat">Chat Room</option>
                </select>
            </div>

            <div class="form-group">
                <label for="room-description">Description (Optional)</label>
                <textarea id="room-description" placeholder="Room description..." rows="2"></textarea>
            </div>

            <button class="btn btn-success" onclick="createRoom()">
                <i class="fas fa-plus"></i> Create Room
            </button>
        </div>
    </div>

    <div class="modal" id="add-friend-modal">
        <div class="settings-modal-content">
            <button class="close-btn" onclick="hideAddFriendModal()">
                <i class="fas fa-times"></i>
            </button>
            
            <div class="settings-header">
                <h2><i class="fas fa-user-plus"></i> Add Friend</h2>
            </div>

            <div class="form-group">
                <label for="friend-username">Username</label>
                <input type="text" id="friend-username" placeholder="Enter username">
            </div>

            <button class="btn btn-success" onclick="sendFriendRequest()">
                <i class="fas fa-user-plus"></i> Send Friend Request
            </button>
        </div>
    </div>

    <div class="modal" id="friend-requests-modal">
        <div class="settings-modal-content">
            <button class="close-btn" onclick="hideFriendRequestsModal()">
                <i class="fas fa-times"></i>
            </button>
            
            <div class="settings-header">
                <h2><i class="fas fa-user-clock"></i> Friend Requests</h2>
            </div>

            <div id="friend-requests-list" style="max-height: 300px; overflow-y: auto;"></div>
        </div>
    </div>

    <div class="modal" id="invite-modal">
        <div class="settings-modal-content" style="max-width: 500px;">
            <button class="close-btn" onclick="hideInviteModal()">
                <i class="fas fa-times"></i>
            </button>
            
            <div class="settings-header">
                <h2><i class="fas fa-link"></i> Invite Friends</h2>
            </div>

            <p>Share this link with your friends:</p>
            
            <div class="invite-link-box" id="invite-link">
                Loading...
            </div>

            <button class="btn" onclick="copyInviteLink()">
                <i class="fas fa-copy"></i> Copy Link
            </button>
        </div>
    </div>

    <!-- NEW: Add Friend to Room Modal -->
    <div class="modal" id="add-friend-to-room-modal">
        <div class="settings-modal-content" style="max-width: 500px;">
            <button class="close-btn" onclick="hideAddFriendToRoomModal()">
                <i class="fas fa-times"></i>
            </button>
            
            <div class="settings-header">
                <h2><i class="fas fa-user-plus"></i> Add Friend to Room</h2>
            </div>

            <div class="form-group">
                <label for="room-friend-select">Select Friend to Add</label>
                <select id="room-friend-select" class="friend-room-select">
                    <option value="">Select a friend...</option>
                </select>
            </div>

            <button class="btn btn-success" onclick="addFriendToRoom()">
                <i class="fas fa-user-plus"></i> Add to Room
            </button>
        </div>
    </div>

    <div class="modal" id="upgrade-modal">
        <div class="settings-modal-content">
            <button class="close-btn" onclick="hideUpgradeModal()">
                <i class="fas fa-times"></i>
            </button>
            
            <div class="settings-header">
                <h2><i class="fas fa-crown"></i> Upgrade to Premium</h2>
                <p>Unlock exclusive features with monthly subscription</p>
            </div>

            <div style="text-align: center; margin-bottom: 30px;">
                <div style="font-size: 48px; color: #ffd700; margin-bottom: 20px;">
                    <i class="fas fa-crown"></i>
                </div>
                <h3 style="color: #ffd700; margin-bottom: 20px;">Premium Features</h3>
                <ul style="text-align: left; margin-bottom: 30px; padding-left: 20px;">
                    <li style="margin-bottom: 10px;">Custom profile banner</li>
                    <li style="margin-bottom: 10px;">HD avatar uploads</li>
                    <li style="margin-bottom: 10px;">Special badge on profile</li>
                    <li style="margin-bottom: 10px;">Create unlimited rooms</li>
                    <li style="margin-bottom: 10px;">Priority support</li>
                </ul>
            </div>

            <div class="form-group">
                <label for="upgrade-code">Enter Secret Code</label>
                <input type="password" id="upgrade-code" placeholder="Enter secret code">
            </div>

            <button class="btn btn-premium" onclick="upgradeAccount()">
                <i class="fas fa-crown"></i> Activate Premium
            </button>
        </div>
    </div>

    <div id="notification-container"></div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.min.js"></script>
    <script>
        let socket;
        let currentUser = '';
        let currentUserEmail = '';
        let isPremium = false;
        let currentRoom = 'general';
        let currentRoomType = 'public';
        let currentRoomData = null;
        let userSettings = {};
        let friendRequests = [];
        let inCall = false;
        let isRoomCreator = false;
        let sessionToken = '';
        let friends = [];
        let privateChats = {};

        // Voice recording variables
        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;
        let recordingStartTime = null;
        let recordingTimer = null;
        let recordingStream = null;

        // Initialize WebSocket
        function initWebSocket() {
            socket = io();
            
            socket.on('connect', () => {
                console.log('✅ Connected to EchoRoom');
                showNotification('Connected to EchoRoom!', 'success');
                
                // Try auto-login with saved session
                tryAutoLogin();
            });

socket.on('message_sent', (data) => {
    console.log('✅ MESSAGE SENT CONFIRMATION:', data);
    
    
    if (data.type === 'private') {
        console.log('📝 Adding sent private message immediately');
        addMessage({
            id: data.id || 'temp-' + Date.now(),
            username: currentUser,
            displayName: userSettings.displayName || currentUser,
            message: data.message,
            server: currentRoom,
            timestamp: data.timestamp || new Date().toISOString(),
            type: 'private'
        });
    }
});

            socket.on('disconnect', () => {
                console.log('❌ Disconnected from server');
                showNotification('Disconnected from server', 'error');
            });

            // Auto-login events
            socket.on('auto_login_success', (data) => {
                console.log('✅ Auto-login success:', data);
                handleLoginSuccess(data);
            });

            socket.on('auto_login_error', (data) => {
                console.log('❌ Auto-login failed');
                // Show auth modal if auto-login fails
                document.getElementById('auth-modal').style.display = 'flex';
            });

            // Login/Signup events
            socket.on('login_success', (data) => {
                console.log('✅ Login success:', data);
                handleLoginSuccess(data);
                
                // Save session if remember me is checked
                const rememberMe = document.getElementById('remember-me')?.checked || 
                                  document.getElementById('remember-signup')?.checked;
                if (rememberMe && data.session_token) {
                    saveSession(data.email, data.session_token, data.username);
                }
            });

            socket.on('login_error', (data) => {
                console.log('❌ Login error:', data);
                showNotification(data.message || 'Login failed', 'error');
            });

            socket.on('signup_success', (data) => {
                console.log('✅ Signup success:', data);
                showNotification('Account created! Welcome email sent. Please login.', 'success');
                showAuthTab('login', null);
                
                // Auto-fill email
                document.getElementById('login-email').value = data.email;
            });

            socket.on('signup_error', (data) => {
                console.log('❌ Signup error:', data);
                showNotification(data.message || 'Signup failed', 'error');
            });

            // Session events
            socket.on('session_expired', (data) => {
                console.log('❌ Session expired');
                showNotification('Session expired. Please login again.', 'error');
                clearSession();
                document.getElementById('auth-modal').style.display = 'flex';
            });

            // Messages
            socket.on('message', (data) => {
                console.log('📨 New message:', data);
                addMessage(data);
            });

            socket.on('chat_messages', (messages) => {
                console.log('📨 Chat messages loaded:', messages?.length);
                const messagesDiv = document.getElementById('chat-messages');
                messagesDiv.innerHTML = '';
                if (messages && messages.length > 0) {
                    messages.forEach(msg => addMessage(msg));
                }
            });

            socket.on('message_deleted', (data) => {
                console.log('🗑️ Message deleted:', data);
                const messageDiv = document.querySelector(`[data-message-id="${data.message_id}"]`);
                if (messageDiv) {
                    messageDiv.innerHTML = '<div style="opacity: 0.5; font-style: italic; padding: 10px;">Message deleted</div>';
                }
            });

            // Private chat messages - ULTRA FIXED VERSION
socket.on('private_message', (data) => {
    console.log('📨🔥 PRIVATE MESSAGE RECEIVED - DEBUG:', data);
    
    // Create consistent room ID
    const sortedUsers = [data.from, data.to].sort();
    const consistentRoomId = `dm_${sortedUsers[0]}_${sortedUsers[1]}`;
    
    console.log('🔍 Debug info:');
    console.log('- From:', data.from);
    console.log('- To:', data.to);
    console.log('- Consistent Room ID:', consistentRoomId);
    console.log('- Current Room:', currentRoom);
    console.log('- Data Room ID:', data.room_id);
    
    // Check if this message is for current chat
    if (currentRoom === consistentRoomId || currentRoom === data.room_id) {
        console.log('✅✅✅ Adding private message to current chat');
        addMessage({
            id: data.id || Date.now().toString(),
            username: data.from,
            displayName: data.displayName || data.from,
            message: data.message,
            server: consistentRoomId,
            timestamp: data.timestamp || new Date().toISOString(),
            type: 'private'
        });
    } else {
        console.log('📨 Private message received but not in current chat');
        // Show notification for new private message
        showNotification(`📩 New message from ${data.displayName || data.from}: ${data.message.substring(0, 30)}...`, 'info');
        
        // Update friend list to show notification
        if (friends && friends.length > 0) {
            updateFriendsList(friends);
        }
        
        // إضافة علامة على الصديق في القائمة
        const friendIndex = friends.findIndex(f => f.username === data.from);
        if (friendIndex !== -1) {
            friends[friendIndex].hasNewMessage = true;
            updateFriendsList(friends);
        }
    }
});

socket.on('private_messages', (data) => {
    console.log('📨🔥 PRIVATE MESSAGES LOADED - DEBUG:', data);
    const messagesDiv = document.getElementById('chat-messages');
    
    if (!messagesDiv) {
        console.error('❌ messagesDiv not found!');
        return;
    }
    
    messagesDiv.innerHTML = '';
    
    if (data.messages && data.messages.length > 0) {
        console.log(`✅ Loading ${data.messages.length} private messages`);
        data.messages.forEach((msg, index) => {
            console.log(`📝 Message ${index + 1}:`, msg);
            addMessage({
                id: msg.id || Date.now().toString() + index,
                username: msg.from,
                displayName: msg.displayName || msg.from,
                message: msg.message,
                server: msg.room_id || currentRoom,
                timestamp: msg.timestamp || new Date().toISOString(),
                type: 'private'
            });
        });
        
        // التمرير لآخر رسالة
        setTimeout(() => {
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }, 100);
    } else {
        console.log('📨 No private messages found');
        messagesDiv.innerHTML = `
            <div style="
                padding: 40px 20px;
                text-align: center;
                opacity: 0.7;
                font-size: 14px;
            ">
                <i class="fas fa-comment-slash" style="font-size: 32px; margin-bottom: 10px;"></i><br>
                No messages yet<br>
                <small style="opacity: 0.5;">Start the conversation!</small>
            </div>
        `;
    }
});

// أضف هذا الحدث الجديد لمعالجة أخطاء الرسائل الخاصة
socket.on('private_message_error', (data) => {
    console.error('❌ PRIVATE MESSAGE ERROR:', data);
    showNotification(data.message || 'Failed to send private message', 'error');
});

// أضف هذا الحدث لمعالجة أخطاء تحميل الرسائل
socket.on('private_messages_error', (data) => {
    console.error('❌ PRIVATE MESSAGES ERROR:', data);
    showNotification(data.message || 'Failed to load messages', 'error');
});

// أضف هذا الحدث لتأكيد إرسال الرسالة
socket.on('private_message_sent', (data) => {
    console.log('✅ Private message sent confirmation:', data);
    // يمكنك إضافة مؤشر إرسال ناجح هنا
});

// Voice messages
            socket.on('voice_message', (data) => {
                console.log('🎤 Voice message received:', data);
                addVoiceMessage(data);
            });

            socket.on('private_voice_message', (data) => {
                console.log('🎤 Private voice message received:', data);
                
                const sortedUsers = [data.from, data.to].sort();
                const consistentRoomId = `dm_${sortedUsers[0]}_${sortedUsers[1]}`;
                
                if (currentRoom === consistentRoomId || currentRoom === data.room_id) {
                    console.log('✅ Adding private voice message to current chat');
                    addVoiceMessage({
                        id: data.id || Date.now().toString(),
                        username: data.from,
                        displayName: data.displayName || data.from,
                        audioData: data.audioData,
                        duration: data.duration,
                        timestamp: data.timestamp || new Date().toISOString(),
                        type: 'voice'
                    });
                } else {
                    showNotification(`🎤 New voice message from ${data.displayName || data.from}`, 'info');
                }
            });

// ========== تحديث دالة addMessage ==========
// تأكد من وجود هذه الدالة المعدلة:
function addMessage(data) {
    console.log('🖊️ Adding message to chat:', {
        id: data.id,
        from: data.username,
        message: data.message.substring(0, 30) + '...'
    });
    
    const messagesDiv = document.getElementById('chat-messages');
    if (!messagesDiv) {
        console.error('❌ Cannot add message: messagesDiv not found');
        return;
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${data.username === currentUser ? 'own' : ''}`;
    messageDiv.setAttribute('data-message-id', data.id);
    messageDiv.style.position = 'relative';
    messageDiv.style.animation = 'slideIn 0.3s ease';
    
    // Check if current user can delete this message
    const canDelete = data.username === currentUser;
    
    // Get first letter for avatar
    const firstLetter = data.username ? data.username.charAt(0).toUpperCase() : 'U';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <div class="avatar-placeholder" style="background: ${data.username === currentUser ? 'rgba(0, 229, 255, 0.3)' : 'rgba(67, 181, 129, 0.3)'};">
                ${firstLetter}
            </div>
        </div>
        <div class="message-content">
            <div class="message-bubble" style="${data.username === currentUser ? 'background: rgba(0, 229, 255, 0.15);' : ''}">
                <div class="message-header">
                    <strong>${data.displayName || data.username || 'Unknown'}</strong>
                    <span>${new Date(data.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                </div>
                <div class="message-text">${escapeHtml(data.message)}</div>
            </div>
            ${canDelete ? `
            <div class="message-actions">
                <button class="msg-action-btn" onclick="deleteMessage('${data.id}')" title="Delete Message">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            ` : ''}
        </div>
    `;
    
    messagesDiv.appendChild(messageDiv);
    
    // التمرير لآخر رسالة
    setTimeout(() => {
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }, 50);
    
    console.log('✅ Message added successfully');
}

// ========== تحديث دالة joinPrivateChat ==========
function joinPrivateChat(friend, roomId) {
    console.log('🚪🔥 JOINING PRIVATE CHAT - DEBUG:', { friend, roomId });
    
    // تحديث المتغيرات
    currentRoom = roomId;
    currentRoomData = { type: 'dm', id: roomId };
    
    // تحديث الواجهة
    document.getElementById('current-chat-name').innerHTML = 
        `<i class="fas fa-user-friends" style="color: #43b581"></i> ${friend}`;
    
    // إظهار رسالة تحميل
    const messagesDiv = document.getElementById('chat-messages');
    messagesDiv.innerHTML = `
        <div style="padding: 30px; text-align: center; opacity: 0.7;">
            <i class="fas fa-spinner fa-spin"></i> Loading messages...
        </div>
    `;
    
    // إعلام السيرفر بالانضمام للغرفة
    socket.emit('join_room', {
        username: currentUser,
        room: roomId
    });
    
    // طلب الرسائل
    console.log('📤 Requesting private messages for friend:', friend);
    socket.emit('get_private_messages', {
        username: currentUser,
        friend: friend
    });
    
    // تحديث رأس الغرفة
    updateRoomHeader();
    
    // تنظيف إشعارات الرسائل الجديدة
    const friendIndex = friends.findIndex(f => f.username === friend);
    if (friendIndex !== -1 && friends[friendIndex].hasNewMessage) {
        friends[friendIndex].hasNewMessage = false;
        updateFriendsList(friends);
    }
    
    console.log('✅✅✅ Successfully joined private chat');
}

            // User settings
            socket.on('user_settings', (settings) => {
                console.log('⚙️ User settings loaded:', settings);
                userSettings = settings || {};
                loadUserSettings();
            });

            socket.on('user_settings_updated', (data) => {
                console.log('✅ Settings updated');
                showNotification('Settings saved!', 'success');
            });

            // Rooms
            socket.on('room_list', (rooms) => {
                console.log('🏠 Rooms loaded:', rooms);
                updateRoomList(rooms);
            });

            socket.on('room_created', (data) => {
                console.log('✅ Room created:', data.room);
                addRoomToList(data.room);
                showNotification(`Room "${data.room.name}" created!`, 'success');
                hideCreateRoomModal();
            });

            socket.on('room_joined', (data) => {
                console.log('✅ Room joined:', data);
                currentRoomData = data.room;
                if (data.room) {
                    currentRoomType = data.room.type;
                }
                updateRoomHeader();
                updateRoomMembers(data.members || []);
            });

            socket.on('room_left', (data) => {
                console.log('✅ Left room:', data);
                showNotification(data.message || 'Left room', 'info');
                if (currentRoom !== 'general' && !currentRoom.startsWith('dm_')) {
                    currentRoom = 'general';
                    joinRoom('general', 'General');
                }
            });

            socket.on('room_deleted', (data) => {
                console.log('🗑️ Room deleted:', data);
                showNotification(data.message || 'Room deleted', 'info');
                if (currentRoom !== 'general' && !currentRoom.startsWith('dm_')) {
                    currentRoom = 'general';
                    joinRoom('general', 'General');
                }
            });

            socket.on('room_join_error', (data) => {
                console.log('❌ Room join error:', data);
                showNotification(data.message || 'Cannot join room', 'error');
            });

            socket.on('invite_link', (data) => {
                console.log('🔗 Invite link:', data);
                document.getElementById('invite-link').textContent = data.link;
            });

            socket.on('invite_link_error', (data) => {
                console.log('❌ Invite link error:', data);
                showNotification(data.message || 'Cannot generate invite', 'error');
            });

            socket.on('room_members_updated', (members) => {
                console.log('👥 Room members updated:', members);
                updateRoomMembers(members);
            });

            // Friends
            socket.on('friends_list', (data) => {
                console.log('👥 Friends loaded:', data);
                friends = data.friends || [];
                updateFriendsList(friends);
            });

            socket.on('friend_request_sent', (data) => {
                console.log('✅ Friend request sent');
                showNotification('Friend request sent!', 'success');
                hideAddFriendModal();
            });

            socket.on('friend_request_error', (data) => {
                console.log('❌ Friend request error');
                showNotification(data.message || 'Friend request failed', 'error');
            });

            socket.on('friend_requests', (data) => {
                console.log('📬 Friend requests:', data.requests);
                friendRequests = data.requests || [];
                updateFriendRequestsList();
                updateFriendRequestsBadge();
            });

            socket.on('friend_request_received', (data) => {
                console.log('📬 Friend request received:', data);
                showNotification(`${data.from} sent you a friend request!`, 'info');
                socket.emit('get_friend_requests', { username: currentUser });
            });

            socket.on('friend_request_accepted', (data) => {
                console.log('✅ Friend request accepted:', data);
                showNotification(`${data.friend} accepted your friend request!`, 'success');
            });

            socket.on('friend_added', (data) => {
                console.log('✅ Friend added:', data);
                showNotification(`You are now friends with ${data.friend}!`, 'success');
                // Automatically create a private chat room
                createPrivateChatRoom(data.friend);
                socket.emit('get_friends', { username: currentUser });
            });

            socket.on('friend_removed', (data) => {
                console.log('🗑️ Friend removed:', data);
                showNotification(`Removed ${data.friend} from friends`, 'info');
                socket.emit('get_friends', { username: currentUser });
            });

            // Premium
            socket.on('premium_activated', (data) => {
                console.log('✅ Premium activated');
                isPremium = true;
                updateUserPremiumStatus(true);
                showNotification('Premium activated for 30 days!', 'success');
                hideUpgradeModal();
            });

            socket.on('premium_error', (data) => {
                console.log('❌ Premium error');
                showNotification(data.message || 'Premium activation failed', 'error');
            });

            // Call events
            socket.on('call_started', (data) => {
                console.log('📞 Call started:', data);
                showNotification(`${data.from} is calling you!`, 'info');
                inCall = true;
                updateCallButton();
            });

            socket.on('call_ended', (data) => {
                console.log('📞 Call ended:', data);
                inCall = false;
                updateCallButton();
                showNotification('Call ended', 'info');
            });

            socket.on('call_error', (data) => {
                console.log('❌ Call error:', data);
                showNotification(data.message || 'Call failed', 'error');
            });

            // Security events
            socket.on('password_changed', (data) => {
                console.log('✅ Password changed');
                showNotification('Password changed successfully!', 'success');
                document.getElementById('current-password').value = '';
                document.getElementById('new-password').value = '';
                document.getElementById('confirm-new-password').value = '';
            });

            socket.on('password_error', (data) => {
                console.log('❌ Password change error');
                showNotification(data.message || 'Password change failed', 'error');
            });

            socket.on('logged_out_all', (data) => {
                console.log('✅ Logged out all devices');
                showNotification('Logged out from all devices', 'info');
                clearSession();
                location.reload();
            });

            // Room friend events
            socket.on('friend_added_to_room', (data) => {
                console.log('✅ Friend added to room:', data);
                showNotification(`Added ${data.friend} to room`, 'success');
                hideAddFriendToRoomModal();
            });

            socket.on('friend_added_to_room_error', (data) => {
                console.log('❌ Friend add to room error');
                showNotification(data.message || 'Cannot add friend to room', 'error');
            });

            // Private chat events
            socket.on('private_chat_created', (data) => {
                console.log('✅ Private chat created:', data);
                privateChats[data.friend] = data.room_id;
                addPrivateChatToList(data.friend, data.room_id);
            });

            socket.on('private_chat_error', (data) => {
                console.log('❌ Private chat error:', data);
                showNotification(data.message || 'Private chat error', 'error');
            });

            // Private message error
            socket.on('private_message_error', (data) => {
                console.log('❌ Private message error:', data);
                showNotification(data.message || 'Failed to send private message', 'error');
            });
        }

        // ========== SESSION MANAGEMENT ==========
        function saveSession(email, token, username) {
            const sessionData = {
                email: email,
                token: token,
                username: username,
                timestamp: Date.now()
            };
            localStorage.setItem('echoRoomSession', JSON.stringify(sessionData));
            console.log('💾 Session saved');
        }

        function getSession() {
            const sessionData = localStorage.getItem('echoRoomSession');
            if (!sessionData) return null;
            
            try {
                return JSON.parse(sessionData);
            } catch (e) {
                return null;
            }
        }

        function clearSession() {
            localStorage.removeItem('echoRoomSession');
            console.log('🗑️ Session cleared');
        }

        function tryAutoLogin() {
            const session = getSession();
            if (session && session.email && session.token) {
                console.log('🔑 Attempting auto-login...');
                socket.emit('auto_login', {
                    email: session.email,
                    token: session.token
                });
            } else {
                console.log('❌ No saved session found');
                document.getElementById('auth-modal').style.display = 'flex';
            }
        }

        // ========== VALIDATION FUNCTIONS ==========
        function validateEmail(input, hintId) {
            const email = input.value.trim();
            const hint = document.getElementById(hintId);
            const emailRegex = /^[a-zA-Z0-9._%+-]+@gmail\.com$/;
            
            if (!email) {
                hint.className = 'email-hint';
                hint.innerHTML = '<i class="fas fa-info-circle"></i> Must be a valid Gmail address';
                return false;
            }
            
            if (emailRegex.test(email)) {
                hint.className = 'email-hint valid';
                hint.innerHTML = '<i class="fas fa-check-circle"></i> Valid Gmail address';
                return true;
            } else {
                hint.className = 'email-hint invalid';
                hint.innerHTML = '<i class="fas fa-exclamation-circle"></i> Must be a @gmail.com address';
                return false;
            }
        }

        function validateUsername(input) {
            const username = input.value.trim();
            const hint = document.getElementById('username-hint');
            const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
            
            if (!username) {
                hint.className = 'email-hint';
                hint.innerHTML = '<i class="fas fa-info-circle"></i> 3-20 characters, letters and numbers only';
                return false;
            }
            
            if (usernameRegex.test(username)) {
                hint.className = 'email-hint valid';
                hint.innerHTML = '<i class="fas fa-check-circle"></i> Valid username';
                return true;
            } else {
                hint.className = 'email-hint invalid';
                hint.innerHTML = '<i class="fas fa-exclamation-circle"></i> 3-20 characters, letters/numbers/underscore only';
                return false;
            }
        }

        function validatePassword(input) {
            const password = input.value;
            const hint = document.getElementById('password-hint');
            
            if (!password) {
                hint.className = 'email-hint';
                hint.innerHTML = '<i class="fas fa-info-circle"></i> Minimum 8 characters';
                return false;
            }
            
            if (password.length >= 8) {
                hint.className = 'email-hint valid';
                hint.innerHTML = '<i class="fas fa-check-circle"></i> Strong password';
                return true;
            } else {
                hint.className = 'email-hint invalid';
                hint.innerHTML = '<i class="fas fa-exclamation-circle"></i> Password must be at least 8 characters';
                return false;
            }
        }

        function validatePasswordConfirm(input) {
            const password = document.getElementById('signup-password').value;
            const confirmPassword = input.value;
            const passwordHint = document.getElementById('password-hint');
            
            if (!confirmPassword) return false;
            
            if (password === confirmPassword) {
                passwordHint.className = 'email-hint valid';
                passwordHint.innerHTML = '<i class="fas fa-check-circle"></i> Passwords match';
                return true;
            } else {
                passwordHint.className = 'email-hint invalid';
                passwordHint.innerHTML = '<i class="fas fa-exclamation-circle"></i> Passwords do not match';
                return false;
            }
        }

        // ========== AUTHENTICATION FUNCTIONS ==========
        function showAuthTab(tabName, event) {
            document.querySelectorAll('.auth-section').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.auth-tab').forEach(btn => {
                btn.classList.remove('active');
            });
            
            document.getElementById(`${tabName}-section`).classList.add('active');
            if (event && event.target) {
                event.target.classList.add('active');
            }
            
            // Focus first input
            if (tabName === 'login') {
                document.getElementById('login-email').focus();
            } else {
                document.getElementById('signup-username').focus();
            }
        }

        function hideAuthModal() {
            document.getElementById('auth-modal').style.display = 'none';
        }

        function login() {
            const email = document.getElementById('login-email').value.trim();
            const password = document.getElementById('login-password').value.trim();
            const rememberMe = document.getElementById('remember-me').checked;
            
            if (!email || !password) {
                showNotification('Please fill all fields', 'error');
                return;
            }
            
            if (!validateEmail(document.getElementById('login-email'), 'login-email-hint')) {
                showNotification('Please enter a valid Gmail address', 'error');
                return;
            }
            
            console.log('🔑 Attempting login with:', email);
            socket.emit('login', { 
                email: email, 
                password: password,
                remember_me: rememberMe
            });
        }

        function signup() {
            const username = document.getElementById('signup-username').value.trim();
            const email = document.getElementById('signup-email').value.trim();
            const password = document.getElementById('signup-password').value;
            const confirmPassword = document.getElementById('signup-password-confirm').value;
            const rememberMe = document.getElementById('remember-signup').checked;
            
            if (!username || !email || !password || !confirmPassword) {
                showNotification('Please fill all fields', 'error');
                return;
            }
            
            if (!validateUsername(document.getElementById('signup-username'))) {
                showNotification('Invalid username format', 'error');
                return;
            }
            
            if (!validateEmail(document.getElementById('signup-email'), 'signup-email-hint')) {
                showNotification('Please enter a valid Gmail address', 'error');
                return;
            }
            
            if (!validatePassword(document.getElementById('signup-password'))) {
                showNotification('Password must be at least 8 characters', 'error');
                return;
            }
            
            if (!validatePasswordConfirm(document.getElementById('signup-password-confirm'))) {
                showNotification('Passwords do not match', 'error');
                return;
            }
            
            console.log('📝 Attempting signup:', { username, email });
            socket.emit('signup', { 
                username: username, 
                email: email, 
                password: password,
                remember_me: rememberMe
            });
        }

        function handleLoginSuccess(data) {
            console.log('🎉 Login success handler triggered');
            currentUser = data.username;
            currentUserEmail = data.email;
            isPremium = data.premium || false;
            sessionToken = data.session_token || '';
            
            // Update UI
            document.getElementById('auth-modal').style.display = 'none';
            document.getElementById('main-app').style.display = 'flex';
            document.getElementById('username-display').textContent = currentUser;
            
            // Update security tab with email
            if (document.getElementById('security-email')) {
                document.getElementById('security-email').value = currentUserEmail;
            }
            
            updateUserPremiumStatus(isPremium);
            
            // Load data
            socket.emit('get_user_settings', { username: currentUser });
            socket.emit('get_rooms');
            socket.emit('get_friends', { username: currentUser });
            socket.emit('get_friend_requests', { username: currentUser });
            
            // Join general room
            socket.emit('join_room', {
                username: currentUser,
                room: 'general'
            });
            
            // Load messages for general room
            socket.emit('get_room_messages', { room: 'general' });
            
            showNotification(`Welcome ${currentUser}!`, 'success');
        }

        // ========== SECURITY FUNCTIONS ==========
        function changePassword() {
            const currentPass = document.getElementById('current-password').value;
            const newPass = document.getElementById('new-password').value;
            const confirmPass = document.getElementById('confirm-new-password').value;
            
            if (!currentPass || !newPass || !confirmPass) {
                showNotification('Please fill all password fields', 'error');
                return;
            }
            
            if (newPass.length < 8) {
                showNotification('New password must be at least 8 characters', 'error');
                return;
            }
            
            if (newPass !== confirmPass) {
                showNotification('New passwords do not match', 'error');
                return;
            }
            
            socket.emit('change_password', {
                email: currentUserEmail,
                current_password: currentPass,
                new_password: newPass,
                session_token: sessionToken
            });
        }

        function logoutAllDevices() {
            if (confirm('Logout from all devices? This will invalidate all active sessions.')) {
                socket.emit('logout_all_devices', {
                    email: currentUserEmail,
                    session_token: sessionToken
                });
            }
        }

        function logout() {
            if (confirm('Logout from this device?')) {
                clearSession();
                location.reload();
            }
        }

        // ========== SETTINGS FUNCTIONS ==========
        function showSettingsModal() {
            document.getElementById('settings-modal').style.display = 'flex';
            loadUserSettings();
        }

        function hideSettingsModal() {
            document.getElementById('settings-modal').style.display = 'none';
        }

        function showSettingsTab(tabName, event) {
            document.querySelectorAll('.settings-section').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.settings-tab').forEach(btn => {
                btn.classList.remove('active');
            });
            
            document.getElementById(`${tabName}-tab`).classList.add('active');
            if (event && event.target) {
                event.target.classList.add('active');
            }
        }

        function loadUserSettings() {
            // Load display name
            const displayNameInput = document.getElementById('display-name');
            const userBioInput = document.getElementById('user-bio');
            const themeSelect = document.getElementById('theme-select');
            const securityEmail = document.getElementById('security-email');
            
            displayNameInput.value = userSettings.displayName || currentUser || '';
            userBioInput.value = userSettings.bio || '';
            themeSelect.value = userSettings.theme || 'dark';
            
            if (securityEmail && currentUserEmail) {
                securityEmail.value = currentUserEmail;
            }
            
            // Update avatar preview
            const avatarPreview = document.getElementById('settings-avatar-preview');
            const userAvatarPreview = document.getElementById('user-avatar-preview');
            
            if (userSettings.avatar) {
                if (userSettings.avatar.startsWith('data:image')) {
                    avatarPreview.innerHTML = `<img src="${userSettings.avatar}" alt="Avatar">`;
                    userAvatarPreview.innerHTML = `<img src="${userSettings.avatar}" alt="Avatar">`;
                } else {
                    avatarPreview.innerHTML = `<div class="avatar-placeholder">${userSettings.avatar}</div>`;
                    userAvatarPreview.innerHTML = `<div class="avatar-placeholder">${userSettings.avatar}</div>`;
                }
            }
            
            // Update banner preview
            const bannerPreview = document.getElementById('settings-banner-preview');
            const bannerLabel = document.getElementById('banner-upload-label');
            const bannerInput = document.getElementById('banner-upload');
            
            if (userSettings.banner && isPremium) {
                bannerPreview.innerHTML = `<img src="${userSettings.banner}" alt="Banner">`;
            }
            
            if (!isPremium) {
                bannerLabel.innerHTML = '<i class="fas fa-lock"></i> Premium Feature';
                bannerLabel.style.opacity = '0.7';
                bannerLabel.style.cursor = 'not-allowed';
                bannerInput.disabled = true;
            } else {
                bannerLabel.innerHTML = '<i class="fas fa-upload"></i> Upload Banner';
                bannerLabel.style.opacity = '1';
                bannerLabel.style.cursor = 'pointer';
                bannerInput.disabled = false;
            }
        }

        function updateUserPremiumStatus(premium) {
            isPremium = premium;
            const premiumBadge = document.getElementById('premium-badge');
            const upgradeBtn = document.getElementById('upgrade-btn');
            
            if (premium) {
                premiumBadge.style.display = 'inline-block';
                upgradeBtn.style.display = 'none';
                document.getElementById('user-status').textContent = '👑 Premium User';
                document.getElementById('user-status').style.color = '#ffd700';
            } else {
                premiumBadge.style.display = 'none';
                upgradeBtn.style.display = 'block';
                document.getElementById('user-status').textContent = 'Free User';
                document.getElementById('user-status').style.color = '';
            }
        }

        function handleAvatarUpload(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const avatarData = e.target.result;
                
                // Update preview
                const avatarPreview = document.getElementById('settings-avatar-preview');
                avatarPreview.innerHTML = `<img src="${avatarData}" alt="Avatar">`;
                
                // Add overlay back
                const avatarOverlay = document.createElement('div');
                avatarOverlay.className = 'avatar-overlay';
                avatarOverlay.innerHTML = '<i class="fas fa-camera"></i> Change Avatar';
                avatarOverlay.onclick = () => document.getElementById('avatar-upload').click();
                avatarPreview.appendChild(avatarOverlay);
                
                // Save to user settings
                userSettings.avatar = avatarData;
                
                showNotification('Avatar updated! Click Save to keep changes.', 'success');
            };
            reader.readAsDataURL(file);
        }

        function handleBannerUpload(event) {
            if (!isPremium) {
                showNotification('Banner upload is a premium feature!', 'error');
                return;
            }
            
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const bannerData = e.target.result;
                
                // Update preview
                const bannerPreview = document.getElementById('settings-banner-preview');
                bannerPreview.innerHTML = `<img src="${bannerData}" alt="Banner">`;
                
                // Save to user settings
                userSettings.banner = bannerData;
                
                showNotification('Banner updated! Click Save to keep changes.', 'success');
            };
            reader.readAsDataURL(file);
        }

        function saveProfileSettings() {
            const displayName = document.getElementById('display-name').value.trim() || currentUser;
            const bio = document.getElementById('user-bio').value.trim();
            
            userSettings.displayName = displayName;
            userSettings.bio = bio;
            
            socket.emit('update_user_settings', {
                username: currentUser,
                settings: userSettings
            });
            
            // Update UI
            document.getElementById('username-display').textContent = displayName;
        }

        function saveAppearanceSettings() {
            const theme = document.getElementById('theme-select').value;
            userSettings.theme = theme;
            
            socket.emit('update_user_settings', {
                username: currentUser,
                settings: userSettings
            });
        }

        // ========== CHAT FUNCTIONS ==========
function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message || !currentUser) {
        console.log('❌ Cannot send empty message or user not logged in');
        showNotification('Cannot send empty message', 'error');
        return;
    }
    
    console.log('📤📤📤 SENDING MESSAGE - DEBUG:', {
        message: message,
        currentRoom: currentRoom,
        currentUser: currentUser,
        isDM: currentRoom.startsWith('dm_')
    });
    
    // Check if we're in a private chat (DM)
    if (currentRoom.startsWith('dm_')) {
        const parts = currentRoom.split('_');
        let friendUsername;
        
        if (parts.length === 3) {
            const [_, user1, user2] = parts;
            friendUsername = user1 === currentUser ? user2 : user1;
        } else {
            console.error('❌ Invalid DM room format:', currentRoom);
            showNotification('Cannot send message: Invalid chat room', 'error');
            return;
        }
        
        console.log('📤 Sending private message to:', friendUsername);
        
        socket.emit('private_message', {
            from: currentUser,
            to: friendUsername,
            message: message,
            timestamp: new Date().toISOString()
        });
        
    } else {
        // Regular room message
        console.log('📤 Sending room message to:', currentRoom);
        socket.emit('message', {
            username: currentUser,
            message: message,
            server: currentRoom,
            timestamp: new Date().toISOString()
        });
    }
    
    // تنظيف حقل الإدخال
    input.value = '';
    input.focus();
}

// ✅✅ دالة addMessage واحدة فقط - مع فحص التكرار
function addMessage(data) {
    console.log('🖊️ Adding message to chat:', {
        id: data.id,
        from: data.username,
        message: data.message.substring(0, 30) + '...'
    });
    
    const messagesDiv = document.getElementById('chat-messages');
    if (!messagesDiv) {
        console.error('❌ Cannot add message: messagesDiv not found');
        return;
    }
    
    // ✅ تحقق من عدم تكرار الرسالة
    const messageId = data.id || data.timestamp;
    const existingMessage = messagesDiv.querySelector(`[data-message-id="${messageId}"]`);
    if (existingMessage) {
        console.log('⚠️ Message already exists, skipping:', messageId);
        return;
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${data.username === currentUser ? 'own' : ''}`;
    messageDiv.setAttribute('data-message-id', messageId);
    messageDiv.style.position = 'relative';
    messageDiv.style.animation = 'slideIn 0.3s ease';
    
    const canDelete = data.username === currentUser;
    const firstLetter = data.username ? data.username.charAt(0).toUpperCase() : 'U';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <div class="avatar-placeholder" style="background: ${data.username === currentUser ? 'rgba(0, 229, 255, 0.3)' : 'rgba(67, 181, 129, 0.3)'};">
                ${firstLetter}
            </div>
        </div>
        <div class="message-content">
            <div class="message-bubble" style="${data.username === currentUser ? 'background: rgba(0, 229, 255, 0.15);' : ''}">
                <div class="message-header">
                    <strong>${data.displayName || data.username || 'Unknown'}</strong>
                    <span>${new Date(data.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                </div>
                <div class="message-text">${escapeHtml(data.message)}</div>
            </div>
            ${canDelete ? `
            <div class="message-actions">
                <button class="msg-action-btn" onclick="deleteMessage('${messageId}')" title="Delete Message">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            ` : ''}
        </div>
    `;
    
    messagesDiv.appendChild(messageDiv);
    
    setTimeout(() => {
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }, 50);
    
    console.log('✅ Message added successfully');
}

function deleteMessage(messageId) {
    if (confirm('Delete this message?')) {
        socket.emit('delete_message', {
            message_id: messageId,
            room_id: currentRoom,
            username: currentUser
        });
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========== VOICE MESSAGE FUNCTIONS ==========
        async function startVoiceRecording() {
            if (isRecording) return;
            
            try {
                recordingStream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    } 
                });
                
                mediaRecorder = new MediaRecorder(recordingStream, {
                    mimeType: 'audio/webm;codecs=opus'
                });
                
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                
                mediaRecorder.onstop = () => {
                    sendVoiceMessage();
                };
                
                mediaRecorder.start();
                isRecording = true;
                recordingStartTime = Date.now();
                
                document.getElementById('voice-record-btn').classList.add('recording');
                document.getElementById('voice-recording-indicator').classList.add('active');
                document.getElementById('voice-cancel-btn').classList.add('active');
                
                updateRecordingTimer();
                recordingTimer = setInterval(updateRecordingTimer, 1000);
                
                console.log('🎤 Voice recording started');
                
            } catch (error) {
                console.error('❌ Error accessing microphone:', error);
                showNotification('Cannot access microphone. Please grant permission.', 'error');
            }
        }

        function stopVoiceRecording() {
            if (!isRecording || !mediaRecorder) return;
            
            const duration = Date.now() - recordingStartTime;
            if (duration < 1000) {
                cancelVoiceRecording();
                showNotification('Recording too short. Hold for at least 1 second.', 'error');
                return;
            }
            
            mediaRecorder.stop();
            isRecording = false;
            
            if (recordingStream) {
                recordingStream.getTracks().forEach(track => track.stop());
            }
            
            if (recordingTimer) {
                clearInterval(recordingTimer);
                recordingTimer = null;
            }
            
            document.getElementById('voice-record-btn').classList.remove('recording');
            document.getElementById('voice-recording-indicator').classList.remove('active');
            document.getElementById('voice-cancel-btn').classList.remove('active');
            
            console.log('🎤 Voice recording stopped');
        }

        function cancelVoiceRecording() {
            if (!isRecording) return;
            
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }
            
            isRecording = false;
            audioChunks = [];
            
            if (recordingStream) {
                recordingStream.getTracks().forEach(track => track.stop());
            }
            
            if (recordingTimer) {
                clearInterval(recordingTimer);
                recordingTimer = null;
            }
            
            document.getElementById('voice-record-btn').classList.remove('recording');
            document.getElementById('voice-recording-indicator').classList.remove('active');
            document.getElementById('voice-cancel-btn').classList.remove('active');
            
            showNotification('Recording cancelled', 'info');
            console.log('🎤 Voice recording cancelled');
        }

        function updateRecordingTimer() {
            if (!recordingStartTime) return;
            
            const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            
            document.getElementById('recording-timer').textContent = 
                `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            if (elapsed >= 60) {
                stopVoiceRecording();
            }
        }

        async function sendVoiceMessage() {
            if (audioChunks.length === 0) return;
            
            try {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm;codecs=opus' });
                const duration = Math.floor((Date.now() - recordingStartTime) / 1000);
                
                const reader = new FileReader();
                reader.onloadend = () => {
                    const base64Audio = reader.result;
                    
                    console.log('📤 Sending voice message:', {
                        size: audioBlob.size,
                        duration: duration,
                        room: currentRoom
                    });
                    
                    if (currentRoom.startsWith('dm_')) {
                        const parts = currentRoom.split('_');
                        if (parts.length === 3) {
                            const [_, user1, user2] = parts;
                            const friendUsername = user1 === currentUser ? user2 : user1;
                            
                            socket.emit('private_voice_message', {
                                from: currentUser,
                                to: friendUsername,
                                audioData: base64Audio,
                                duration: duration,
                                timestamp: new Date().toISOString()
                            });
                        }
                    } else {
                        socket.emit('voice_message', {
                            username: currentUser,
                            server: currentRoom,
                            audioData: base64Audio,
                            duration: duration,
                            timestamp: new Date().toISOString()
                        });
                    }
                    
                    showNotification('Voice message sent!', 'success');
                };
                
                reader.readAsDataURL(audioBlob);
                
            } catch (error) {
                console.error('❌ Error sending voice message:', error);
                showNotification('Failed to send voice message', 'error');
            }
        }

        function addVoiceMessage(data) {
            console.log('🎤 Adding voice message to chat');
            
            const messagesDiv = document.getElementById('chat-messages');
            if (!messagesDiv) return;
            
            const messageId = data.id || data.timestamp;
            const existingMessage = messagesDiv.querySelector(`[data-message-id="${messageId}"]`);
            if (existingMessage) {
                console.log('⚠️ Voice message already exists, skipping');
                return;
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${data.username === currentUser ? 'own' : ''}`;
            messageDiv.setAttribute('data-message-id', messageId);
            messageDiv.style.position = 'relative';
            messageDiv.style.animation = 'slideIn 0.3s ease';
            
            const canDelete = data.username === currentUser;
            const firstLetter = data.username ? data.username.charAt(0).toUpperCase() : 'U';
            const audioId = `audio-${messageId}`;
            
            messageDiv.innerHTML = `
                <div class="message-avatar">
                    <div class="avatar-placeholder" style="background: ${data.username === currentUser ? 'rgba(0, 229, 255, 0.3)' : 'rgba(67, 181, 129, 0.3)'};">
                        ${firstLetter}
                    </div>
                </div>
                <div class="message-content">
                    <div class="message-bubble" style="${data.username === currentUser ? 'background: rgba(0, 229, 255, 0.15);' : ''}">
                        <div class="message-header">
                            <strong>${data.displayName || data.username || 'Unknown'}</strong>
                            <span>${new Date(data.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                        </div>
                        <div class="voice-message">
                            <button class="voice-play-btn" onclick="toggleVoicePlayback('${audioId}', this)">
                                <i class="fas fa-play"></i>
                            </button>
                            <div class="voice-waveform">
                                <div class="voice-progress" id="progress-${audioId}" style="width: 0%"></div>
                            </div>
                            <span class="voice-duration">${formatDuration(data.duration || 0)}</span>
                            <audio id="${audioId}" src="${data.audioData}" preload="metadata" style="display: none;"></audio>
                        </div>
                    </div>
                    ${canDelete ? `
                    <div class="message-actions">
                        <button class="msg-action-btn" onclick="deleteMessage('${messageId}')" title="Delete Message">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                    ` : ''}
                </div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            
            const audio = document.getElementById(audioId);
            if (audio) {
                audio.addEventListener('timeupdate', () => {
                    const progress = (audio.currentTime / audio.duration) * 100;
                    const progressBar = document.getElementById(`progress-${audioId}`);
                    if (progressBar) {
                        progressBar.style.width = `${progress}%`;
                    }
                });
                
                audio.addEventListener('ended', () => {
                    const btn = messageDiv.querySelector('.voice-play-btn');
                    if (btn) {
                        btn.classList.remove('playing');
                        btn.innerHTML = '<i class="fas fa-play"></i>';
                    }
                    const progressBar = document.getElementById(`progress-${audioId}`);
                    if (progressBar) {
                        progressBar.style.width = '0%';
                    }
                });
            }
            
            setTimeout(() => {
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }, 50);
            
            console.log('✅ Voice message added successfully');
        }

        function toggleVoicePlayback(audioId, button) {
            const audio = document.getElementById(audioId);
            if (!audio) return;
            
            document.querySelectorAll('audio').forEach(a => {
                if (a.id !== audioId && !a.paused) {
                    a.pause();
                    a.currentTime = 0;
                }
            });
            
            document.querySelectorAll('.voice-play-btn').forEach(btn => {
                if (btn !== button) {
                    btn.classList.remove('playing');
                    btn.innerHTML = '<i class="fas fa-play"></i>';
                }
            });
            
            if (audio.paused) {
                audio.play();
                button.classList.add('playing');
                button.innerHTML = '<i class="fas fa-pause"></i>';
            } else {
                audio.pause();
                button.classList.remove('playing');
                button.innerHTML = '<i class="fas fa-play"></i>';
            }
        }

        function formatDuration(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }
// ========== ROOM FUNCTIONS ==========
function updateRoomList(rooms) {
    const list = document.getElementById('servers-list');
    list.innerHTML = '';
    
    // Add private chats first
    Object.keys(privateChats).forEach(friend => {
        const roomDiv = document.createElement('div');
        roomDiv.className = 'nav-item';
        roomDiv.innerHTML = `
            <i class="fas fa-user-friends" style="color: #43b581"></i>
            <span>${friend}</span>
            <span class="room-type-badge dm">DM</span>
        `;
        
        roomDiv.onclick = () => {
            joinPrivateChat(friend, privateChats[friend]);
        };
        
        list.appendChild(roomDiv);
    });
    
    // Add separator if there are both private chats and rooms
    if (Object.keys(privateChats).length > 0 && rooms && rooms.length > 0) {
        const separator = document.createElement('div');
        separator.style.padding = '10px';
        separator.style.opacity = '0.7';
        separator.style.textAlign = 'center';
        separator.innerHTML = '─ ROOMS ─';
        list.appendChild(separator);
    }
    
    if (!rooms || rooms.length === 0) {
        if (Object.keys(privateChats).length === 0) {
            list.innerHTML = '<div style="padding: 10px; opacity: 0.7; text-align: center;">No rooms yet</div>';
        }
        return;
    }
    
    rooms.forEach(room => {
        addRoomToList(room);
    });
}

function addRoomToList(room) {
    const list = document.getElementById('servers-list');
    const roomDiv = document.createElement('div');
    roomDiv.className = 'nav-item';
    
    let icon = 'fa-hashtag';
    if (room.type === 'voice') icon = 'fa-volume-up';
    if (room.type === 'private') icon = 'fa-lock';
    
    roomDiv.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${room.name}</span>
        ${room.type !== 'public' ? `<span class="room-type-badge ${room.type}">${room.type}</span>` : ''}
    `;
    
    roomDiv.onclick = () => {
        joinRoom(room.id, room.name);
    };
    
    list.appendChild(roomDiv);
}

function addPrivateChatToList(friend, roomId) {
    const list = document.getElementById('servers-list');
    
    // Check if already exists
    const existing = Array.from(list.children).find(item => 
        item.textContent.includes(friend) && item.textContent.includes('DM')
    );
    
    if (!existing) {
        const roomDiv = document.createElement('div');
        roomDiv.className = 'nav-item';
        roomDiv.innerHTML = `
            <i class="fas fa-user-friends" style="color: #43b581"></i>
            <span>${friend}</span>
            <span class="room-type-badge dm">DM</span>
        `;
        
        roomDiv.onclick = () => {
            joinPrivateChat(friend, roomId);
        };
        
        // Insert at the beginning (before rooms)
        const firstRoom = list.querySelector('.nav-item:not([style*="opacity: 0.7"])');
        if (firstRoom) {
            list.insertBefore(roomDiv, firstRoom);
        } else {
            list.appendChild(roomDiv);
        }
    }
}

function joinRoom(roomId, roomName) {
    console.log('🚪 Joining room:', roomId, roomName);
    currentRoom = roomId;
    document.getElementById('current-chat-name').innerHTML = 
        `<i class="fas fa-hashtag"></i> ${roomName}`;
    
    document.getElementById('chat-messages').innerHTML = '';
    
    socket.emit('join_room', { 
        room: roomId, 
        username: currentUser 
    });
    
    socket.emit('get_room_messages', { room: roomId });
    
    // Update room header
    updateRoomHeader();
}

function joinPrivateChat(friend, roomId) {
    console.log('🚪 Joining private chat with:', friend);
    
    // Create consistent room ID
    const sortedUsers = [currentUser, friend].sort();
    const consistentRoomId = `dm_${sortedUsers[0]}_${sortedUsers[1]}`;
    currentRoom = consistentRoomId;
    
    document.getElementById('current-chat-name').innerHTML = 
        `<i class="fas fa-user-friends" style="color: #43b581"></i> ${friend}`;
    
    document.getElementById('chat-messages').innerHTML = '';
    
    // Load private messages
    socket.emit('get_private_messages', {
        username: currentUser,
        friend: friend
    });
    
    // Join the private chat room
    socket.emit('join_room', {
        username: currentUser,
        room: consistentRoomId
    });
    
    // Update room header for DM
    updateRoomHeader();
    
    console.log('✅ Joined private chat:', consistentRoomId);
}

        function updateRoomHeader() {
            const actions = document.getElementById('room-header-actions');
            const deleteBtn = document.getElementById('delete-room-btn');
            const callBtn = document.getElementById('call-btn');
            const addFriendBtn = document.getElementById('add-friend-to-room-btn');
            
            if (currentRoom.startsWith('dm_')) {
                // Private chat
                actions.style.display = 'flex';
                deleteBtn.style.display = 'none';
                callBtn.style.display = 'inline-flex';
                addFriendBtn.style.display = 'none';
                isRoomCreator = false;
            } else if (currentRoom !== 'general') {
                // Regular room
                actions.style.display = 'flex';
                
                // Show delete button only for room creator
                if (currentRoomData && currentRoomData.creator === currentUser) {
                    deleteBtn.style.display = 'inline-flex';
                    isRoomCreator = true;
                } else {
                    deleteBtn.style.display = 'none';
                    isRoomCreator = false;
                }
                
                // Show call button only for private rooms
                if (currentRoomData && currentRoomData.type === 'private') {
                    callBtn.style.display = 'inline-flex';
                } else {
                    callBtn.style.display = 'none';
                }
                
                // Show add friend button for room creator
                if (currentRoomData && currentRoomData.creator === currentUser && currentRoomData.type === 'private') {
                    addFriendBtn.style.display = 'inline-flex';
                } else {
                    addFriendBtn.style.display = 'none';
                }
            } else {
                // General room
                actions.style.display = 'none';
            }
            
            updateCallButton();
        }

        function updateCallButton() {
            const callBtn = document.getElementById('call-btn');
            if (callBtn) {
                if (inCall) {
                    callBtn.innerHTML = '<i class="fas fa-phone-slash"></i> End Call';
                    callBtn.style.background = 'rgba(255, 46, 99, 0.2)';
                    callBtn.style.borderColor = 'rgba(255, 46, 99, 0.5)';
                } else {
                    callBtn.innerHTML = '<i class="fas fa-phone"></i> Call';
                    callBtn.style.background = 'rgba(67, 181, 129, 0.1)';
                    callBtn.style.borderColor = 'rgba(67, 181, 129, 0.3)';
                }
            }
        }

        function toggleCall() {
            if (inCall) {
                endCall();
            } else {
                startCall();
            }
        }

        function startCall() {
            socket.emit('start_call', {
                from: currentUser,
                room_id: currentRoom
            });
        }

        function endCall() {
            socket.emit('end_call', {
                room_id: currentRoom
            });
        }

        function leaveRoom() {
            if (currentRoom === 'general') {
                showNotification('Cannot leave general room', 'error');
                return;
            }
            
            if (confirm('Leave this room?')) {
                socket.emit('leave_room', {
                    username: currentUser,
                    room_id: currentRoom
                });
            }
        }

        function deleteRoom() {
            if (!isRoomCreator) {
                showNotification('Only room creator can delete room', 'error');
                return;
            }
            
            if (confirm('Delete this room? This action cannot be undone.')) {
                socket.emit('delete_room', {
                    username: currentUser,
                    room_id: currentRoom
                });
            }
        }

        function updateRoomMembers(members) {
            const membersDiv = document.getElementById('room-members');
            membersDiv.innerHTML = '';
            
            if (!members || members.length === 0) {
                membersDiv.innerHTML = '<div style="padding: 10px; opacity: 0.7; text-align: center;">No members</div>';
                return;
            }
            
            members.forEach(member => {
                const memberDiv = document.createElement('div');
                memberDiv.className = 'nav-item';
                memberDiv.innerHTML = `
                    <i class="fas fa-user" style="color: ${member.connected ? '#43b581' : '#888'}"></i>
                    <span>${member.username}</span>
                    ${member.username === currentUser ? '<span style="margin-left: auto; font-size: 12px; opacity: 0.7;">You</span>' : ''}
                `;
                membersDiv.appendChild(memberDiv);
            });
        }

        // ========== CREATE ROOM FUNCTIONS ==========
        function showCreateRoomModal() {
            document.getElementById('create-room-modal').style.display = 'flex';
            document.getElementById('room-name').focus();
        }

        function hideCreateRoomModal() {
            document.getElementById('create-room-modal').style.display = 'none';
            document.getElementById('room-name').value = '';
            document.getElementById('room-description').value = '';
            document.getElementById('room-type').value = 'public';
        }

        function createRoom() {
            const name = document.getElementById('room-name').value.trim();
            const description = document.getElementById('room-description').value.trim();
            const type = document.getElementById('room-type').value;
            
            if (!name) {
                showNotification('Room name is required', 'error');
                return;
            }
            
            socket.emit('create_room', {
                name: name,
                description: description,
                type: type,
                creator: currentUser
            });
        }

        // ========== FRIEND FUNCTIONS ==========
        function showAddFriendModal() {
            document.getElementById('add-friend-modal').style.display = 'flex';
            document.getElementById('friend-username').focus();
        }

        function hideAddFriendModal() {
            document.getElementById('add-friend-modal').style.display = 'none';
            document.getElementById('friend-username').value = '';
        }

        function sendFriendRequest() {
            const friendUsername = document.getElementById('friend-username').value.trim();
            
            if (!friendUsername) {
                showNotification('Please enter a username', 'error');
                return;
            }
            
            if (friendUsername === currentUser) {
                showNotification('You cannot add yourself', 'error');
                return;
            }
            
            socket.emit('send_friend_request', {
                from: currentUser,
                to: friendUsername
            });
        }

        function showFriendRequestsModal() {
    console.log('🔄 Opening friend requests modal for user:', currentUser);
    
    // إظهار النافذة
    document.getElementById('friend-requests-modal').style.display = 'flex';
    
    // تنظيف القائمة وإظهار رسالة تحميل
    const list = document.getElementById('friend-requests-list');
    list.innerHTML = '<div style="padding: 30px; text-align: center; opacity: 0.7;">Loading friend requests...</div>';
    
    // طلب البيانات من السيرفر
    if (currentUser) {
        console.log('📤 Sending get_friend_requests for:', currentUser);
        socket.emit('get_friend_requests', { 
            username: currentUser 
        });
    } else {
        console.log('❌ Cannot get friend requests: No current user');
        list.innerHTML = '<div style="padding: 30px; text-align: center; opacity: 0.7;">Please login first</div>';
    }
}

        function hideFriendRequestsModal() {
            document.getElementById('friend-requests-modal').style.display = 'none';
        }

        function updateFriendRequestsList() {
            const list = document.getElementById('friend-requests-list');
            list.innerHTML = '';
            
            if (friendRequests.length === 0) {
                list.innerHTML = '<div style="padding: 20px; text-align: center; opacity: 0.7;">No friend requests</div>';
                return;
            }
            
            friendRequests.forEach(request => {
                const requestDiv = document.createElement('div');
                requestDiv.style.padding = '15px';
                requestDiv.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
                requestDiv.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>${request}</strong>
                            <div style="font-size: 12px; opacity: 0.7;">Wants to be your friend</div>
                        </div>
                        <div>
                            <button class="action-btn" onclick="acceptFriendRequest('${request}')" title="Accept">
                                <i class="fas fa-check"></i> Accept
                            </button>
                            <button class="action-btn delete" onclick="declineFriendRequest('${request}')" title="Decline">
                                <i class="fas fa-times"></i> Decline
                            </button>
                        </div>
                    </div>
                `;
                list.appendChild(requestDiv);
            });
        }

        function updateFriendsList(friendsList) {
            const friendsContainer = document.getElementById('friends-list');
            friendsContainer.innerHTML = '';
            
            if (!friendsList || friendsList.length === 0) {
                friendsContainer.innerHTML = '<div style="padding: 10px; opacity: 0.7; text-align: center;">No friends yet</div>';
                return;
            }
            
            friendsList.forEach(friend => {
                const friendDiv = document.createElement('div');
                friendDiv.className = 'nav-item';
                friendDiv.innerHTML = `
                    <i class="fas fa-user" style="color: ${friend.connected ? '#43b581' : '#888'}"></i>
                    <span>${friend.username}</span>
                    <span class="friend-status ${friend.connected ? '' : 'offline'}">
                        ${friend.connected ? 'Online' : 'Offline'}
                    </span>
                    <button class="friend-chat-btn" onclick="startPrivateChat('${friend.username}')" title="Chat">
                        <i class="fas fa-comment"></i>
                    </button>
                    <button class="action-btn delete" onclick="removeFriend('${friend.username}')" title="Remove Friend" style="margin-left: auto; padding: 5px 10px; font-size: 12px;">
                        <i class="fas fa-user-minus"></i>
                    </button>
                `;
                friendsContainer.appendChild(friendDiv);
            });
        }

        function acceptFriendRequest(friendUsername) {
            socket.emit('accept_friend_request', {
                username: currentUser,
                friend_username: friendUsername
            });
        }

        function declineFriendRequest(friendUsername) {
            socket.emit('decline_friend_request', {
                username: currentUser,
                friend_username: friendUsername
            });
        }

        function removeFriend(friendUsername) {
            if (confirm(`Remove ${friendUsername} from friends?`)) {
                socket.emit('remove_friend', {
                    username: currentUser,
                    friend_username: friendUsername
                });
            }
        }

        function updateFriendRequestsBadge() {
            const badge = document.getElementById('friend-requests-badge');
            if (friendRequests.length > 0) {
                badge.textContent = friendRequests.length;
                badge.style.display = 'block';
            } else {
                badge.style.display = 'none';
            }
        }

        // ========== PRIVATE CHAT FUNCTIONS ==========
        function createPrivateChatRoom(friendUsername) {
            // Create a consistent room ID for the private chat
            const sortedUsers = [currentUser, friendUsername].sort();
            const roomId = `dm_${sortedUsers[0]}_${sortedUsers[1]}`;
            privateChats[friendUsername] = roomId;
            
            // Add to room list
            addPrivateChatToList(friendUsername, roomId);
            
            // Notify server about private chat creation
            socket.emit('create_private_chat', {
                user1: currentUser,
                user2: friendUsername,
                room_id: roomId
            });
            
            console.log('✅ Created private chat room:', roomId);
            return roomId;
        }

        function startPrivateChat(friendUsername) {
            console.log('💬 Starting private chat with:', friendUsername);
            let roomId = privateChats[friendUsername];
            
            if (!roomId) {
                roomId = createPrivateChatRoom(friendUsername);
            }
            
            joinPrivateChat(friendUsername, roomId);
        }

        // ========== ADD FRIEND TO ROOM FUNCTIONS ==========
        function showAddFriendToRoomModal() {
            const modal = document.getElementById('add-friend-to-room-modal');
            const select = document.getElementById('room-friend-select');
            
            // Clear and populate friend list
            select.innerHTML = '<option value="">Select a friend...</option>';
            
            friends.forEach(friend => {
                if (friend.connected) {
                    const option = document.createElement('option');
                    option.value = friend.username;
                    option.textContent = `${friend.username} (Online)`;
                    select.appendChild(option);
                }
            });
            
            modal.style.display = 'flex';
        }

        function hideAddFriendToRoomModal() {
            document.getElementById('add-friend-to-room-modal').style.display = 'none';
        }

        function addFriendToRoom() {
            const select = document.getElementById('room-friend-select');
            const friendUsername = select.value;
            
            if (!friendUsername) {
                showNotification('Please select a friend', 'error');
                return;
            }
            
            socket.emit('add_friend_to_room', {
                room_id: currentRoom,
                friend_username: friendUsername,
                username: currentUser
            });
        }

        // ========== INVITE FUNCTIONS ==========
        function showInviteModal() {
            document.getElementById('invite-modal').style.display = 'flex';
            socket.emit('get_invite_link', {
                username: currentUser,
                room_id: currentRoom
            });
        }

        function hideInviteModal() {
            document.getElementById('invite-modal').style.display = 'none';
        }

        function copyInviteLink() {
            const linkText = document.getElementById('invite-link').textContent;
            navigator.clipboard.writeText(linkText).then(() => {
                showNotification('Invite link copied!', 'success');
            });
        }

        // ========== UPGRADE FUNCTIONS ==========
        function showUpgradeModal() {
            document.getElementById('upgrade-modal').style.display = 'flex';
            document.getElementById('upgrade-code').focus();
        }

        function hideUpgradeModal() {
            document.getElementById('upgrade-modal').style.display = 'none';
            document.getElementById('upgrade-code').value = '';
        }

        function upgradeAccount() {
            const upgradeCode = document.getElementById('upgrade-code').value.trim();
            
            if (!upgradeCode) {
                showNotification('Enter upgrade code', 'error');
                return;
            }
            
            socket.emit('activate_premium', {
                username: currentUser,
                code: upgradeCode
            });
        }

        // ========== UTILITY FUNCTIONS ==========
        function showNotification(message, type = 'info') {
            const container = document.getElementById('notification-container');
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            container.appendChild(notification);
            
            setTimeout(() => notification.remove(), 3000);
        }

        function toggleMute() {
            const btn = document.getElementById('mute-btn');
            const isMuted = btn.innerHTML.includes('Unmute');
            btn.innerHTML = isMuted ? 
                '<i class="fas fa-microphone"></i> Mute' : 
                '<i class="fas fa-microphone-slash"></i> Unmute';
            showNotification(isMuted ? 'Microphone unmuted' : 'Microphone muted', 'info');
        }

        function toggleDeafen() {
            const btn = document.getElementById('deafen-btn');
            const isDeafened = btn.innerHTML.includes('Undeafen');
            btn.innerHTML = isDeafened ? 
                '<i class="fas fa-headset"></i> Deafen' : 
                '<i class="fas fa-headset"></i> Undeafen';
            showNotification(isDeafened ? 'Undeafened' : 'Deafened', 'info');
        }

        // Debug function
        function debugPrivateChat() {
            console.log('🔍 Debug Private Chat:');
            console.log('- Current User:', currentUser);
            console.log('- Current Room:', currentRoom);
            console.log('- Friends:', friends);
            console.log('- Private Chats:', privateChats);
            console.log('- Socket Connected:', socket.connected);
            
            if (currentRoom.startsWith('dm_')) {
                const parts = currentRoom.split('_');
                if (parts.length === 3) {
                    const [_, user1, user2] = parts;
                    const friend = user1 === currentUser ? user2 : user1;
                    console.log('- Current Friend:', friend);
                    console.log('- Are friends?:', friends.some(f => f.username === friend));
                }
            }
        }

        // ========== INITIALIZATION ==========
        window.onload = function() {
            console.log('🚀 Initializing EchoRoom...');
            initWebSocket();
            
            // Enter key handlers
            document.getElementById('login-email').onkeypress = function(e) {
                if (e.key === 'Enter') login();
            };
            document.getElementById('login-password').onkeypress = function(e) {
                if (e.key === 'Enter') login();
            };
            
            document.getElementById('signup-username').onkeypress = function(e) {
                if (e.key === 'Enter') signup();
            };
            document.getElementById('signup-email').onkeypress = function(e) {
                if (e.key === 'Enter') signup();
            };
            document.getElementById('signup-password').onkeypress = function(e) {
                if (e.key === 'Enter') signup();
            };
            document.getElementById('signup-password-confirm').onkeypress = function(e) {
                if (e.key === 'Enter') signup();
            };
            
            document.getElementById('message-input').onkeypress = function(e) {
                if (e.key === 'Enter') sendMessage();
            };
            
            document.getElementById('room-name').onkeypress = function(e) {
                if (e.key === 'Enter') createRoom();
            };
            
            document.getElementById('friend-username').onkeypress = function(e) {
                if (e.key === 'Enter') sendFriendRequest();
            };
            
            document.getElementById('upgrade-code').onkeypress = function(e) {
                if (e.key === 'Enter') upgradeAccount();
            };
        };
    </script>
</body>
</html>
'''

# Data file and functions
DATA_FILE = 'echoroom_data.json'

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        else:
            print(f"📁 Creating new data file: {DATA_FILE}")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
    
    # Initialize with empty data structure
    return {
        'users_db': {},
        'rooms_db': {},
        'messages_db': {},
        'user_settings': {},
        'friends_db': {},
        'friend_requests_db': {},
        'sessions_db': {},
        'private_messages_db': {}
    }

def save_data():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({
                'users_db': users_db,
                'rooms_db': rooms_db,
                'messages_db': messages_db,
                'user_settings': user_settings_db,
                'friends_db': friends_db,
                'friend_requests_db': friend_requests_db,
                'sessions_db': sessions_db,
                'private_messages_db': private_messages_db
            }, f, indent=2, cls=DateTimeEncoder)  # استخدام الـ encoder المخصص
        print(f"💾 Data saved to {DATA_FILE}")
    except Exception as e:
        print(f"❌ Error saving data: {e}")

# Load data
data = load_data()
users_db = data.get('users_db', {})
rooms_db = data.get('rooms_db', {})
messages_db = data.get('messages_db', {})
user_settings_db = data.get('user_settings', {})
friends_db = data.get('friends_db', {})
friend_requests_db = data.get('friend_requests_db', {})
sessions_db = data.get('sessions_db', {})
private_messages_db = data.get('private_messages_db', {})

active_users = {}
user_rooms = {}
socket_sessions = {}

# Create default room if not exists
if "general" not in rooms_db:
    rooms_db["general"] = {
        'id': 'general',
        'name': 'General',
        'description': 'Welcome to EchoRoom!',
        'type': 'public',
        'creator': 'system',
        'created_at': datetime.now().isoformat(),
        'members': []
    }
    save_data()

# ==================== HELPER FUNCTIONS ====================

def find_user_email(username):
    for email, user_data in users_db.items():
        if user_data.get('username') == username:
            return email
    return None

def get_room_members(room_id):
    room = rooms_db.get(room_id)
    if not room:
        return []
    
    members = []
    for username in room.get('members', []):
        is_connected = username in active_users
        members.append({
            'username': username,
            'connected': is_connected
        })
    
    return members

def are_friends(user1, user2):
    return (user2 in friends_db.get(user1, [])) and (user1 in friends_db.get(user2, []))

def create_session(email):
    """Create a new session for user"""
    token = generate_session_token()
    expiry = datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)
    
    if email not in sessions_db:
        sessions_db[email] = []
    
    sessions_db[email].append({
        'token': token,
        'created_at': datetime.now().isoformat(),
        'expires_at': expiry.isoformat(),
        'ip': request.remote_addr if request else 'unknown'
    })
    
    # Keep only last 5 sessions per user
    if len(sessions_db[email]) > 5:
        sessions_db[email] = sessions_db[email][-5:]
    
    save_data()
    return token

def validate_session(email, token):
    """Validate user session token"""
    if email not in sessions_db:
        return False
    
    now = datetime.now()
    valid_sessions = []
    is_valid = False
    
    for session in sessions_db[email]:
        expiry = datetime.fromisoformat(session['expires_at'])
        if expiry > now and session['token'] == token:
            is_valid = True
            valid_sessions.append(session)
    
    # Remove expired sessions
    sessions_db[email] = valid_sessions
    save_data()
    
    return is_valid

def invalidate_all_sessions(email):
    """Invalidate all sessions for a user"""
    if email in sessions_db:
        sessions_db[email] = []
        save_data()
        return True
    return False

def get_private_chat_key(user1, user2):
    """Get a consistent key for private messages between two users"""
    # Sort usernames to ensure consistent key regardless of order
    sorted_users = sorted([user1, user2])
    return f"{sorted_users[0]}_{sorted_users[1]}"

def get_private_messages(user1, user2):
    """Get private messages between two users"""
    key = get_private_chat_key(user1, user2)
    return private_messages_db.get(key, [])

def add_private_message(from_user, to_user, message, timestamp):
    """Add a private message to the database"""
    key = get_private_chat_key(from_user, to_user)
    
    if key not in private_messages_db:
        private_messages_db[key] = []
    
    message_data = {
        'id': str(uuid.uuid4())[:8],
        'from': from_user,
        'to': to_user,
        'message': message,
        'timestamp': timestamp,
        'room_id': f"dm_{from_user}_{to_user}",
        'type': 'private'
    }
    
    private_messages_db[key].append(message_data)
    
    # Keep only last 1000 messages per chat
    if len(private_messages_db[key]) > 1000:
        private_messages_db[key] = private_messages_db[key][-1000:]
    
    save_data()
    
    print(f"📨 Private message saved: {from_user} -> {to_user}: {message[:50]}...")
    return message_data

# ==================== FLASK ROUTES ====================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/favicon.ico')
def favicon():
    return '', 404

# ==================== SOCKETIO EVENTS ====================

@socketio.on('connect')
def handle_connect():
    print(f"✅ Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    # Remove from active users
    for username, sid in list(active_users.items()):
        if sid == request.sid:
            del active_users[username]
            if username in user_rooms:
                del user_rooms[username]
            print(f"❌ User disconnected: {username}")
            
            # Notify rooms user was in
            for room_id, room in rooms_db.items():
                if username in room.get('members', []):
                    socketio.emit('room_members_updated', 
                                get_room_members(room_id),
                                room=room_id)
            break
    
    # Remove socket session
    if request.sid in socket_sessions:
        del socket_sessions[request.sid]

@socketio.on('auto_login')
def handle_auto_login(data):
    email = data.get('email')
    token = data.get('token')
    
    if not email or not token:
        emit('auto_login_error', {'message': 'Invalid session'})
        return
    
    if not validate_session(email, token):
        emit('auto_login_error', {'message': 'Session expired'})
        return
    
    if email not in users_db:
        emit('auto_login_error', {'message': 'User not found'})
        return
    
    user_data = users_db[email]
    username = user_data.get('username')
    
    if not username:
        emit('auto_login_error', {'message': 'Invalid user data'})
        return
    
    # Store session
    socket_sessions[request.sid] = {
        'email': email,
        'token': token,
        'username': username
    }
    
    active_users[username] = request.sid
    
    emit('auto_login_success', {
        'username': username,
        'email': email,
        'premium': user_data.get('premium', False),
        'session_token': token
    })

@socketio.on('signup')
def handle_signup(data):
    username = data.get('username', '').strip()
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    remember_me = data.get('remember_me', True)
    
    # Validation
    if not username or not email or not password:
        emit('signup_error', {'message': 'All fields required'})
        return
    
    if not is_valid_gmail(email):
        emit('signup_error', {'message': 'Please use a valid Gmail address (@gmail.com)'})
        return
    
    # Check if email already exists
    if email in users_db:
        emit('signup_error', {'message': 'Email already registered'})
        return
    
    # Check if username already exists
    for user_data in users_db.values():
        if user_data.get('username') == username:
            emit('signup_error', {'message': 'Username already taken'})
            return
    
    # Hash password
    hashed_password, salt = hash_password(password)
    
    # Create user
    users_db[email] = {
        'username': username,
        'password_hash': hashed_password,
        'salt': salt,
        'premium': False,
        'created_at': datetime.now().isoformat(),
        'verified': False
    }
    
    # Initialize user data structures
    friends_db[username] = []
    friend_requests_db[username] = []
    user_settings_db[username] = {
        'displayName': username,
        'avatar': None,
        'banner': None,
        'bio': '',
        'theme': 'dark'
    }
    
    # Create session if remember me is enabled
    session_token = None
    if remember_me:
        session_token = create_session(email)
    
    save_data()
    
    # Send welcome email
    send_welcome_email(email, username)
    
    emit('signup_success', {
        'message': 'Account created successfully',
        'email': email,
        'session_token': session_token
    })

@socketio.on('login')
def handle_login(data):
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    remember_me = data.get('remember_me', True)
    
    if email not in users_db:
        emit('login_error', {'message': 'Invalid email or password'})
        return
    
    user_data = users_db[email]
    
    # Verify password
    if not verify_password(password, user_data['password_hash'], user_data['salt']):
        emit('login_error', {'message': 'Invalid email or password'})
        return
    
    username = user_data['username']
    
    # Create session
    session_token = None
    if remember_me:
        session_token = create_session(email)
    
    # Store session
    socket_sessions[request.sid] = {
        'email': email,
        'token': session_token,
        'username': username
    }
    
    active_users[username] = request.sid
    
    emit('login_success', {
        'username': username,
        'email': email,
        'premium': user_data.get('premium', False),
        'session_token': session_token
    })

@socketio.on('change_password')
def handle_change_password(data):
    email = data.get('email')
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    token = data.get('session_token')
    
    if not validate_session(email, token):
        emit('session_expired', {'message': 'Session expired'})
        return
    
    if email not in users_db:
        emit('password_error', {'message': 'User not found'})
        return
    
    user_data = users_db[email]
    
    # Verify current password
    if not verify_password(current_password, user_data['password_hash'], user_data['salt']):
        emit('password_error', {'message': 'Current password is incorrect'})
        return
    
    # Hash new password
    hashed_password, salt = hash_password(new_password)
    
    # Update password
    users_db[email]['password_hash'] = hashed_password
    users_db[email]['salt'] = salt
    
    save_data()
    
    emit('password_changed', {'success': True})

@socketio.on('logout_all_devices')
def handle_logout_all(data):
    email = data.get('email')
    token = data.get('session_token')
    
    if not validate_session(email, token):
        emit('session_expired', {'message': 'Session expired'})
        return
    
    # Invalidate all sessions
    invalidate_all_sessions(email)
    
    # Disconnect user if online
    username = users_db[email]['username']
    if username in active_users:
        sid = active_users[username]
        socketio.emit('logged_out_all', {}, room=sid)
        del active_users[username]
    
    emit('logged_out_all', {'success': True})

# ========== SECURITY MIDDLEWARE ==========
def check_auth(sid):
    """Check if socket has valid authentication"""
    if sid not in socket_sessions:
        return None
    
    session = socket_sessions[sid]
    email = session['email']
    token = session['token']
    
    if not validate_session(email, token):
        return None
    
    return session

# ========== PROTECTED SOCKET EVENTS ==========

@socketio.on('join_room')
def handle_join_room(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    room_id = data.get('room')
    
    if not room_id:
        emit('room_join_error', {'message': 'Room ID required'})
        return
    
    # Check if it's a private chat room
    if room_id.startswith('dm_'):
        # Extract usernames from room ID
        parts = room_id.split('_')
        if len(parts) == 3:
            user1, user2 = parts[1], parts[2]
            
            # Check if user is part of this DM
            if username not in [user1, user2]:
                emit('room_join_error', {'message': 'Not authorized to join this private chat'})
                return
            
            # Use the room ID as is (already sorted in client)
            join_room(room_id)
            user_rooms[username] = room_id
            
            print(f"✅ {username} joined private chat: {room_id}")
            
            emit('room_joined', {
                'room': {'id': room_id, 'type': 'dm'},
                'members': []
            })
        return
    
    # Regular room joining logic
    if username in active_users:
        room = rooms_db.get(room_id)
        if room and room.get('type') == 'private':
            if room.get('creator') != username and username not in room.get('invited', []):
                creator = room.get('creator')
                if not are_friends(username, creator):
                    emit('room_join_error', {'message': 'Private room. You need to be friends with the creator.'})
                    return
        
        join_room(room_id)
        user_rooms[username] = room_id
        
        if room_id in rooms_db:
            room = rooms_db[room_id]
            if username not in room.get('members', []):
                room['members'] = room.get('members', []) + [username]
                save_data()
        
        print(f"✅ {username} joined room: {room_id}")
        
        emit('room_joined', {
            'room': rooms_db.get(room_id, {}),
            'members': get_room_members(room_id)
        })
        
        socketio.emit('room_members_updated', 
                     get_room_members(room_id),
                     room=room_id)

@socketio.on('leave_room')
def handle_leave_room(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    room_id = data.get('room_id')
    
    if not room_id:
        emit('room_left', {'message': 'Room ID required'})
        return
    
    if room_id == 'general':
        emit('room_left', {'message': 'Cannot leave general room'})
        return
    
    # Don't leave private chat rooms from database
    if not room_id.startswith('dm_'):
        if room_id in rooms_db:
            room = rooms_db[room_id]
            if username in room.get('members', []):
                room['members'] = [m for m in room['members'] if m != username]
                save_data()
    
    leave_room(room_id)
    
    if username in user_rooms and user_rooms[username] == room_id:
        del user_rooms[username]
    
    if not room_id.startswith('dm_'):
        socketio.emit('room_members_updated', 
                     get_room_members(room_id),
                     room=room_id)
    
    emit('room_left', {
        'room_id': room_id,
        'message': f'Left room {rooms_db.get(room_id, {}).get("name", "")}'
    })

@socketio.on('delete_room')
def handle_delete_room(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    room_id = data.get('room_id')
    
    if not room_id:
        emit('room_deleted', {'message': 'Room ID required'})
        return
    
    if room_id == 'general':
        emit('room_deleted', {'message': 'Cannot delete general room'})
        return
    
    # Don't allow deleting private chat rooms
    if room_id.startswith('dm_'):
        emit('room_deleted', {'message': 'Cannot delete private chats'})
        return
    
    if room_id in rooms_db:
        room = rooms_db[room_id]
        if room.get('creator') != username:
            emit('room_deleted', {'message': 'Only room creator can delete room'})
            return
        
        socketio.emit('room_deleted', {
            'room_id': room_id,
            'message': 'Room has been deleted by the creator'
        }, room=room_id)
        
        del rooms_db[room_id]
        
        if room_id in messages_db:
            del messages_db[room_id]
        
        save_data()
        
        socketio.emit('room_list', list(rooms_db.values()), broadcast=True)
        
        emit('room_deleted', {
            'room_id': room_id,
            'message': 'Room deleted successfully'
        })

@socketio.on('get_invite_link')
def handle_get_invite_link(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    room_id = data.get('room_id')
    
    if not room_id:
        emit('invite_link_error', {'message': 'Room ID required'})
        return
    
    if room_id.startswith('dm_'):
        emit('invite_link_error', {'message': 'Cannot generate invite links for private chats'})
        return
    
    if room_id in rooms_db:
        room = rooms_db[room_id]
        if room.get('type') == 'private' and room.get('creator') != username:
            emit('invite_link_error', {'message': 'Only room creator can generate invite links'})
            return
        
        invite_link = f"http://localhost:5000/join/{room_id}"
        emit('invite_link', {'link': invite_link})

@socketio.on('message')
def handle_message(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    message_text = data.get('message', '').strip()
    server = data.get('server')
    
    if not message_text or not server:
        return
    
    message_id = str(uuid.uuid4())[:8]
    user_settings = user_settings_db.get(username, {})
    
    message = {
        'id': message_id,
        'username': username,
        'displayName': user_settings.get('displayName', username),
        'message': message_text,
        'server': server,
        'timestamp': data.get('timestamp', datetime.now().isoformat()),
        'type': 'server'
    }
    
    if server not in messages_db:
        messages_db[server] = []
    messages_db[server].append(message)
    
    if len(messages_db[server]) > 500:
        messages_db[server] = messages_db[server][-500:]
    
    save_data()
    
    print(f"📨 Room message sent: {username} -> {server}: {message_text[:50]}...")
    emit('message', message, room=server)

@socketio.on('voice_message')
def handle_voice_message(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    audio_data = data.get('audioData')
    duration = data.get('duration', 0)
    server = data.get('server')
    timestamp = data.get('timestamp', datetime.now().isoformat())
    
    if not audio_data or not server:
        return
    
    message_id = str(uuid.uuid4())[:8]
    user_settings = user_settings_db.get(username, {})
    
    message = {
        'id': message_id,
        'username': username,
        'displayName': user_settings.get('displayName', username),
        'audioData': audio_data,
        'duration': duration,
        'server': server,
        'timestamp': timestamp,
        'type': 'voice'
    }
    
    if server not in messages_db:
        messages_db[server] = []
    messages_db[server].append(message)
    
    if len(messages_db[server]) > 500:
        messages_db[server] = messages_db[server][-500:]
    
    save_data()
    
    print(f"🎤 Voice message sent: {username} -> {server} ({duration}s)")
    emit('voice_message', message, room=server)

@socketio.on('private_voice_message')
def handle_private_voice_message(data):
    print("🎤 SERVER: private_voice_message received")
    
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    from_user = session['username']
    to_user = data.get('to')
    audio_data = data.get('audioData')
    duration = data.get('duration', 0)
    timestamp = data.get('timestamp', datetime.now().isoformat())
    
    if not to_user or not audio_data:
        emit('private_message_error', {'message': 'Missing required fields'})
        return
    
    if not are_friends(from_user, to_user):
        emit('private_message_error', {'message': 'You can only message friends'})
        return
    
    key = get_private_chat_key(from_user, to_user)
    
    if key not in private_messages_db:
        private_messages_db[key] = []
    
    message_id = str(uuid.uuid4())[:8]
    from_settings = user_settings_db.get(from_user, {})
    
    sorted_users = sorted([from_user, to_user])
    room_id = f"dm_{sorted_users[0]}_{sorted_users[1]}"
    
    message_data = {
        'id': message_id,
        'from': from_user,
        'to': to_user,
        'audioData': audio_data,
        'duration': duration,
        'timestamp': timestamp,
        'room_id': room_id,
        'type': 'voice'
    }
    
    private_messages_db[key].append(message_data)
    
    if len(private_messages_db[key]) > 1000:
        private_messages_db[key] = private_messages_db[key][-1000:]
    
    save_data()
    
    formatted_message = {
        'id': message_id,
        'from': from_user,
        'to': to_user,
        'audioData': audio_data,
        'duration': duration,
        'timestamp': timestamp,
        'displayName': from_settings.get('displayName', from_user),
        'room_id': room_id,
        'type': 'voice'
    }
    
    socketio.emit('private_voice_message', formatted_message, room=room_id)
    
    print(f"✅ Private voice message sent: {from_user} -> {to_user} ({duration}s)")

@socketio.on('private_message')
def handle_private_message(data):
    print("🔥🔥🔥 SERVER: private_message received")
    print(f"From: {data.get('from')}")
    print(f"To: {data.get('to')}")
    print(f"Message: {data.get('message')[:50]}...")
    
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    from_user = session['username']
    to_user = data.get('to')
    message_text = data.get('message', '').strip()
    timestamp = data.get('timestamp', datetime.now().isoformat())
    
    if not to_user or not message_text:
        emit('private_message_error', {'message': 'Missing required fields'})
        return
    
    # Check if users are friends
    if not are_friends(from_user, to_user):
        emit('private_message_error', {'message': 'You can only message friends'})
        return
    
    # Save private message
    message_data = add_private_message(from_user, to_user, message_text, timestamp)
    
    # Create consistent room ID (sorted usernames)
    sorted_users = sorted([from_user, to_user])
    room_id = f"dm_{sorted_users[0]}_{sorted_users[1]}"
    
    # Get display names
    from_settings = user_settings_db.get(from_user, {})
    to_settings = user_settings_db.get(to_user, {})
    
    # Prepare message for both users
    formatted_message = {
        'id': message_data['id'],
        'from': from_user,
        'to': to_user,
        'message': message_text,
        'timestamp': timestamp,
        'displayName': from_settings.get('displayName', from_user),
        'room_id': room_id,
        'type': 'private'
    }
    
    print(f"📨 Broadcasting to room: {room_id}")
    print(f"📨 Message data: {formatted_message}")
    
    # إرسال تأكيد للمرسل أولاً
    emit('private_message_sent', {
        'id': message_data['id'],
        'message': message_text,
        'timestamp': timestamp,
        'type': 'private'
    }, room=request.sid)
    
    # ثم إرسال الرسالة للغرفة (للمرسل والمستقبل)
    socketio.emit('private_message', formatted_message, room=room_id)
    
    print(f"✅✅✅ Private message sent successfully: {from_user} -> {to_user}")


@socketio.on('voice_message')
def handle_voice_message(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    audio_data = data.get('audioData')
    duration = data.get('duration', 0)
    server = data.get('server')
    timestamp = data.get('timestamp', datetime.now().isoformat())
    
    if not audio_data or not server:
        return
    
    message_id = str(uuid.uuid4())[:8]
    user_settings = user_settings_db.get(username, {})
    
    message = {
        'id': message_id,
        'username': username,
        'displayName': user_settings.get('displayName', username),
        'audioData': audio_data,
        'duration': duration,
        'server': server,
        'timestamp': timestamp,
        'type': 'voice'
    }
    
    if server not in messages_db:
        messages_db[server] = []
    messages_db[server].append(message)
    
    if len(messages_db[server]) > 500:
        messages_db[server] = messages_db[server][-500:]
    
    save_data()
    
    print(f"🎤 Voice message sent: {username} -> {server} ({duration}s)")
    emit('voice_message', message, room=server)


@socketio.on('private_voice_message')
def handle_private_voice_message(data):
    print("🎤 SERVER: private_voice_message received")
    
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    from_user = session['username']
    to_user = data.get('to')
    audio_data = data.get('audioData')
    duration = data.get('duration', 0)
    timestamp = data.get('timestamp', datetime.now().isoformat())
    
    if not to_user or not audio_data:
        emit('private_message_error', {'message': 'Missing required fields'})
        return
    
    if not are_friends(from_user, to_user):
        emit('private_message_error', {'message': 'You can only message friends'})
        return
    
    key = get_private_chat_key(from_user, to_user)
    
    if key not in private_messages_db:
        private_messages_db[key] = []
    
    message_id = str(uuid.uuid4())[:8]
    from_settings = user_settings_db.get(from_user, {})
    
    sorted_users = sorted([from_user, to_user])
    room_id = f"dm_{sorted_users[0]}_{sorted_users[1]}"
    
    message_data = {
        'id': message_id,
        'from': from_user,
        'to': to_user,
        'audioData': audio_data,
        'duration': duration,
        'timestamp': timestamp,
        'room_id': room_id,
        'type': 'voice'
    }
    
    private_messages_db[key].append(message_data)
    
    if len(private_messages_db[key]) > 1000:
        private_messages_db[key] = private_messages_db[key][-1000:]
    
    save_data()
    
    formatted_message = {
        'id': message_id,
        'from': from_user,
        'to': to_user,
        'audioData': audio_data,
        'duration': duration,
        'timestamp': timestamp,
        'displayName': from_settings.get('displayName', from_user),
        'room_id': room_id,
        'type': 'voice'
    }
    
    socketio.emit('private_voice_message', formatted_message, room=room_id)
    
    print(f"✅ Private voice message sent: {from_user} -> {to_user} ({duration}s)")

@socketio.on('private_voice_message')
def handle_private_voice_message(data):
    print("🎤 SERVER: private_voice_message received")
    
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    from_user = session['username']
    to_user = data.get('to')
    audio_data = data.get('audioData')
    duration = data.get('duration', 0)
    timestamp = data.get('timestamp', datetime.now().isoformat())
    
    if not to_user or not audio_data:
        emit('private_message_error', {'message': 'Missing required fields'})
        return
    
    if not are_friends(from_user, to_user):
        emit('private_message_error', {'message': 'You can only message friends'})
        return
    
    key = get_private_chat_key(from_user, to_user)
    
    if key not in private_messages_db:
        private_messages_db[key] = []
    
    message_id = str(uuid.uuid4())[:8]
    from_settings = user_settings_db.get(from_user, {})
    
    sorted_users = sorted([from_user, to_user])
    room_id = f"dm_{sorted_users[0]}_{sorted_users[1]}"
    
    message_data = {
        'id': message_id,
        'from': from_user,
        'to': to_user,
        'audioData': audio_data,
        'duration': duration,
        'timestamp': timestamp,
        'room_id': room_id,
        'type': 'voice'
    }
    
    private_messages_db[key].append(message_data)
    
    if len(private_messages_db[key]) > 1000:
        private_messages_db[key] = private_messages_db[key][-1000:]
    
    save_data()
    
    formatted_message = {
        'id': message_id,
        'from': from_user,
        'to': to_user,
        'audioData': audio_data,
        'duration': duration,
        'timestamp': timestamp,
        'displayName': from_settings.get('displayName', from_user),
        'room_id': room_id,
        'type': 'voice'
    }
    
    socketio.emit('private_voice_message', formatted_message, room=room_id)
    
    print(f"✅ Private voice message sent: {from_user} -> {to_user} ({duration}s)")



@socketio.on('get_private_messages')
def handle_get_private_messages(data):
    session = check_auth(request.sid)
    if not session:
        return
    
    username = session['username']
    friend = data.get('friend')
    
    if not friend:
        emit('private_messages_error', {'message': 'Friend username required'})
        return
    
    # Check if users are friends
    if not are_friends(username, friend):
        emit('private_messages_error', {'message': 'You can only view messages with friends'})
        return
    
    messages = get_private_messages(username, friend)
    
    # Create consistent room ID
    sorted_users = sorted([username, friend])
    room_id = f"dm_{sorted_users[0]}_{sorted_users[1]}"
    
    # Format messages for display
    formatted_messages = []
    for msg in messages:
        # Get display name from user settings
        from_user_settings = user_settings_db.get(msg['from'], {})
        display_name = from_user_settings.get('displayName', msg['from'])
        
        formatted_messages.append({
            'id': msg['id'],
            'from': msg['from'],
            'to': msg['to'],
            'username': msg['from'],
            'displayName': display_name,
            'message': msg['message'],
            'room_id': room_id,
            'timestamp': msg['timestamp'],
            'type': 'private'
        })
    
    print(f"📨 Retrieved {len(formatted_messages)} private messages between {username} and {friend}")
    emit('private_messages', {
        'friend': friend,
        'room_id': room_id,
        'messages': formatted_messages
    })

@socketio.on('delete_message')
def handle_delete_message(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    message_id = data.get('message_id')
    room_id = data.get('room_id')
    
    if not message_id or not room_id:
        return
    
    # Check if it's a private chat room
    if room_id.startswith('dm_'):
        # Extract usernames from room ID
        parts = room_id.split('_')
        if len(parts) == 3:
            user1, user2 = parts[1], parts[2]
            key = get_private_chat_key(user1, user2)
            
            if key in private_messages_db:
                for i, msg in enumerate(private_messages_db[key]):
                    if msg.get('id') == message_id and msg.get('from') == username:
                        del private_messages_db[key][i]
                        save_data()
                        emit('message_deleted', {'message_id': message_id}, room=room_id)
                        break
    else:
        # Regular room message
        if room_id in messages_db:
            for i, msg in enumerate(messages_db[room_id]):
                if msg.get('id') == message_id:
                    room = rooms_db.get(room_id, {})
                    can_delete = msg.get('username') == username or room.get('creator') == username
                    
                    if can_delete:
                        del messages_db[room_id][i]
                        save_data()
                        emit('message_deleted', {'message_id': message_id}, room=room_id)
                        break

@socketio.on('get_room_messages')
def handle_get_room_messages(data):
    session = check_auth(request.sid)
    if not session:
        return
    
    room_id = data.get('room')
    
    if not room_id:
        return
    
    # Check if it's a private chat room
    if room_id.startswith('dm_'):
        # Extract usernames from room ID
        parts = room_id.split('_')
        if len(parts) == 3:
            user1, user2 = parts[1], parts[2]
            username = session['username']
            
            # Determine which friend this chat is with
            friend = user2 if user1 == username else user1
            
            # Get private messages
            handle_get_private_messages({
                'friend': friend
            })
    else:
        # Regular room messages
        room_messages = messages_db.get(room_id, [])
        emit('chat_messages', room_messages[-100:])

@socketio.on('get_rooms')
def handle_get_rooms():
    session = check_auth(request.sid)
    if not session:
        return
    
    emit('room_list', list(rooms_db.values()))

@socketio.on('create_room')
def handle_create_room(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    room_name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    room_type = data.get('type', 'public')
    
    if not room_name:
        emit('room_created_error', {'message': 'Room name is required'})
        return
    
    room_id = str(uuid.uuid4())[:8]
    room = {
        'id': room_id,
        'name': room_name,
        'description': description,
        'type': room_type,
        'creator': username,
        'created_at': datetime.now().isoformat(),
        'members': [username],
        'invited': []
    }
    
    rooms_db[room_id] = room
    save_data()
    
    if username in active_users:
        join_room(room_id)
    
    emit('room_created', {'room': room})
    socketio.emit('room_list', list(rooms_db.values()), broadcast=True)

@socketio.on('create_private_chat')
def handle_create_private_chat(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    user1 = data.get('user1')
    user2 = data.get('user2')
    room_id = data.get('room_id')
    
    if not user1 or not user2:
        emit('private_chat_error', {'message': 'Both users required'})
        return
    
    # Verify the user is part of this private chat
    if username not in [user1, user2]:
        emit('private_chat_error', {'message': 'Unauthorized'})
        return
    
    # Determine which friend this is
    friend = user2 if user1 == username else user1
    
    # Create room ID if not provided (sorted for consistency)
    if not room_id:
        sorted_users = sorted([user1, user2])
        room_id = f"dm_{sorted_users[0]}_{sorted_users[1]}"
    
    emit('private_chat_created', {
        'friend': friend,
        'room_id': room_id
    })

@socketio.on('get_user_settings')
def handle_get_user_settings(data):
    session = check_auth(request.sid)
    if not session:
        return
    
    username = session['username']
    
    if username not in user_settings_db:
        user_settings_db[username] = {
            'displayName': username,
            'avatar': None,
            'banner': None,
            'bio': '',
            'theme': 'dark'
        }
        save_data()
    
    emit('user_settings', user_settings_db[username])

@socketio.on('update_user_settings')
def handle_update_user_settings(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    settings = data.get('settings', {})
    
    if username not in user_settings_db:
        user_settings_db[username] = {}
    
    user_settings_db[username].update(settings)
    save_data()
    
    emit('user_settings_updated', {'success': True})

@socketio.on('activate_premium')
def handle_activate_premium(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    code = data.get('code', '').strip()
    
    if not code:
        emit('premium_error', {'message': 'Upgrade code required'})
        return
    
    user_email = find_user_email(username)
    if not user_email:
        emit('premium_error', {'message': 'User not found'})
        return
    
    # Premium activation code
    if code != 'The Goat':
        emit('premium_error', {'message': 'Invalid upgrade code'})
        return
    
    users_db[user_email]['premium'] = True
    users_db[user_email]['premium_until'] = (datetime.now() + timedelta(days=30)).isoformat()
    save_data()
    
    emit('premium_activated', {'username': username})

@socketio.on('send_friend_request')
def handle_send_friend_request(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    from_user = session['username']
    to_user = data.get('to', '').strip()
    
    if not to_user:
        emit('friend_request_error', {'message': 'Username required'})
        return
    
    if from_user == to_user:
        emit('friend_request_error', {'message': 'Cannot add yourself'})
        return
    
    # Check if user exists
    user_exists = False
    for user_data in users_db.values():
        if user_data.get('username') == to_user:
            user_exists = True
            break
    
    if not user_exists:
        emit('friend_request_error', {'message': 'User not found'})
        return
    
    # Check if already friends
    if are_friends(from_user, to_user):
        emit('friend_request_error', {'message': 'Already friends'})
        return
    
    # Check if request already sent
    if to_user in friend_requests_db.get(from_user, []):
        emit('friend_request_error', {'message': 'Friend request already sent'})
        return
    
    # Initialize friend requests for recipient if not exists
    if to_user not in friend_requests_db:
        friend_requests_db[to_user] = []
    
    # Check if request already exists
    if from_user not in friend_requests_db[to_user]:
        friend_requests_db[to_user].append(from_user)
        save_data()
    
    # Notify recipient if online
    if to_user in active_users:
        socketio.emit('friend_request_received', {
            'from': from_user
        }, room=active_users[to_user])
    
    emit('friend_request_sent', {'success': True})

@socketio.on('get_friend_requests')
def handle_get_friend_requests(data):
    session = check_auth(request.sid)
    if not session:
        return
    
    username = session['username']
    
    requests = friend_requests_db.get(username, [])
    emit('friend_requests', {'requests': requests})

@socketio.on('accept_friend_request')
def handle_accept_friend_request(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    friend_username = data.get('friend_username', '').strip()
    
    if not friend_username:
        emit('friend_request_error', {'message': 'Friend username required'})
        return
    
    # Check if request exists
    if friend_username not in friend_requests_db.get(username, []):
        emit('friend_request_error', {'message': 'Friend request not found'})
        return
    
    # Remove from friend requests
    friend_requests_db[username] = [r for r in friend_requests_db.get(username, []) if r != friend_username]
    
    # Add to friends lists
    if username not in friends_db:
        friends_db[username] = []
    if friend_username not in friends_db[username]:
        friends_db[username].append(friend_username)
    
    if friend_username not in friends_db:
        friends_db[friend_username] = []
    if username not in friends_db[friend_username]:
        friends_db[friend_username].append(username)
    
    save_data()
    
    # Create room ID for the private chat
    sorted_users = sorted([username, friend_username])
    room_id = f"dm_{sorted_users[0]}_{sorted_users[1]}"
    
    # Notify both users
    if username in active_users:
        # Update friends list for current user
        friends_list = []
        for friend in friends_db.get(username, []):
            is_connected = friend in active_users
            friends_list.append({
                'username': friend,
                'connected': is_connected
            })
        
        emit('friends_list', {'friends': friends_list}, room=active_users[username])
        emit('friend_request_accepted', {'friend': friend_username}, room=active_users[username])
        emit('private_chat_created', {'friend': friend_username, 'room_id': room_id}, room=active_users[username])
    
    if friend_username in active_users:
        # Update friends list for friend
        friends_list = []
        for friend in friends_db.get(friend_username, []):
            is_connected = friend in active_users
            friends_list.append({
                'username': friend,
                'connected': is_connected
            })
        
        emit('friends_list', {'friends': friends_list}, room=active_users[friend_username])
        emit('friend_added', {'friend': username}, room=active_users[friend_username])
        emit('private_chat_created', {'friend': username, 'room_id': room_id}, room=active_users[friend_username])

@socketio.on('decline_friend_request')
def handle_decline_friend_request(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    friend_username = data.get('friend_username', '').strip()
    
    if not friend_username:
        return
    
    if username in friend_requests_db:
        friend_requests_db[username] = [r for r in friend_requests_db[username] if r != friend_username]
        save_data()
    
    if username in active_users:
        emit('friend_request_declined', {
            'friend': friend_username
        }, room=active_users[username])

@socketio.on('remove_friend')
def handle_remove_friend(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    friend_username = data.get('friend_username', '').strip()
    
    if not friend_username:
        emit('friend_removed_error', {'message': 'Friend username required'})
        return
    
    # Remove from friends lists
    if username in friends_db:
        friends_db[username] = [f for f in friends_db[username] if f != friend_username]
    
    if friend_username in friends_db:
        friends_db[friend_username] = [f for f in friends_db[friend_username] if f != username]
    
    save_data()
    
    # Notify both users
    if username in active_users:
        emit('friend_removed', {'friend': friend_username}, room=active_users[username])
        
        # Update friends list
        friends_list = []
        for friend in friends_db.get(username, []):
            is_connected = friend in active_users
            friends_list.append({
                'username': friend,
                'connected': is_connected
            })
        emit('friends_list', {'friends': friends_list}, room=active_users[username])
    
    if friend_username in active_users:
        emit('friend_removed', {'friend': username}, room=active_users[friend_username])
        
        # Update friends list for friend
        friends_list = []
        for friend in friends_db.get(friend_username, []):
            is_connected = friend in active_users
            friends_list.append({
                'username': friend,
                'connected': is_connected
            })
        emit('friends_list', {'friends': friends_list}, room=active_users[friend_username])

@socketio.on('get_friends')
def handle_get_friends(data):
    session = check_auth(request.sid)
    if not session:
        return
    
    username = session['username']
    
    friends_list = []
    for friend in friends_db.get(username, []):
        is_connected = friend in active_users
        friends_list.append({
            'username': friend,
            'connected': is_connected
        })
    
    emit('friends_list', {'friends': friends_list})

@socketio.on('add_friend_to_room')
def handle_add_friend_to_room(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    room_id = data.get('room_id')
    friend_username = data.get('friend_username', '').strip()
    
    if not room_id or not friend_username:
        emit('friend_added_to_room_error', {'message': 'Room ID and friend username required'})
        return
    
    # Check if room exists
    if room_id not in rooms_db:
        emit('friend_added_to_room_error', {'message': 'Room not found'})
        return
    
    room = rooms_db[room_id]
    
    # Check if user is room creator
    if room.get('creator') != username:
        emit('friend_added_to_room_error', {'message': 'Only room creator can add friends'})
        return
    
    # Check if room is private
    if room.get('type') != 'private':
        emit('friend_added_to_room_error', {'message': 'Can only add friends to private rooms'})
        return
    
    # Check if users are friends
    if not are_friends(username, friend_username):
        emit('friend_added_to_room_error', {'message': 'You can only add friends to private rooms'})
        return
    
    # Add friend to room members
    if friend_username not in room.get('members', []):
        room['members'] = room.get('members', []) + [friend_username]
    
    # Add to invited list
    if 'invited' not in room:
        room['invited'] = []
    
    if friend_username not in room['invited']:
        room['invited'].append(friend_username)
    
    save_data()
    
    # Notify friend if online
    if friend_username in active_users:
        socketio.emit('room_invited', {
            'room_id': room_id,
            'room_name': room.get('name'),
            'invited_by': username
        }, room=active_users[friend_username])
    
    emit('friend_added_to_room', {
        'friend': friend_username,
        'room_id': room_id
    })
    
    # Update room members for everyone in the room
    socketio.emit('room_members_updated', 
                 get_room_members(room_id),
                 room=room_id)

@socketio.on('start_call')
def handle_start_call(data):
    session = check_auth(request.sid)
    if not session:
        emit('session_expired', {'message': 'Please login again'})
        return
    
    username = session['username']
    room_id = data.get('room_id')
    
    if not room_id:
        emit('call_error', {'message': 'Room ID required'})
        return
    
    # For private chats, allow calls
    if room_id.startswith('dm_'):
        emit('call_started', {
            'from': username,
            'room_id': room_id
        }, room=room_id, include_self=False)
        return
    
    room = rooms_db.get(room_id, {})
    if room.get('type') != 'private':
        emit('call_error', {'message': 'Calls only allowed in private rooms or DMs'})
        return
    
    emit('call_started', {
        'from': username,
        'room_id': room_id
    }, room=room_id, include_self=False)

@socketio.on('end_call')
def handle_end_call(data):
    session = check_auth(request.sid)
    if not session:
        return
    
    room_id = data.get('room_id')
    
    if not room_id:
        return
    
    emit('call_ended', {
        'room_id': room_id
    }, room=room_id)

if __name__ == '__main__':
    print("=" * 60)
    print("🎤 ECHOROOM - SECURE VERSION (FIXED)")
    print("=" * 60)
    print("\n✅ ALL ISSUES FIXED:")
    print("- Persistent user accounts (saved to echoroom_data.json)")
    print("- Friend requests work correctly")
    print("- Private chat (DM) messages now send and receive properly")
    print("- Auto-login works with 'Remember me'")
    print("- All data persists between sessions")
    print("\n✅ DEBUG FEATURES:")
    print("- Console logs for all private messages")
    print("- Error messages for debugging")
    print("- Consistent room IDs for private chats")
    print("\n🔧 SETUP REQUIRED:")
    print("1. Set EMAIL_SENDER and EMAIL_PASSWORD for Gmail")
    print("2. Enable Gmail App Password")
    print("3. Run: python app.py")
    print("\n🔑 PREMIUM SECRET CODE: 'The Goat'")
    print("\n🚀 Access: http://localhost:5000")
    print("=" * 60)
    
    socketio.run(app, 
                 host='0.0.0.0', 
                 port=5000, 
                 debug=False, 
                 allow_unsafe_werkzeug=True)

