import pyperclip
import re
import time
import threading
import sys
import os
import subprocess
import traceback
from datetime import datetime
import platform

# 检测操作系统类型
SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"
IS_MAC = SYSTEM == "Darwin"

# 根据操作系统导入相应的模块
if IS_WINDOWS:
    import win32con
    import win32gui
    import win32api
    import win32clipboard
    import ctypes
    from ctypes import wintypes
    try:
        import psutil
        import win32process
    except ImportError:
        print("正在安装必要的依赖: psutil和pywin32...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil pywin32"])
        import psutil
        import win32process
elif IS_MAC:
    try:
        import AppKit
        import Quartz
        import Foundation
        import objc
        import psutil
        from PyObjCTools import AppHelper
    except ImportError:
        print("正在安装必要的依赖: pyobjc和psutil...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyobjc psutil"])
        import AppKit
        import Quartz
        import Foundation
        import objc
        import psutil
        from PyObjCTools import AppHelper

# ------------ 配置区域（按需修改）------------
# 敏感数据正则规则（可自定义）
SENSITIVE_PATTERNS = [
    r'\b\d{17}[\dXx]\b',  # 简化的身份证号匹配（18位）
    r'\b\d{15}\b',  # 简化的身份证号匹配（15位旧版）
    r'\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{2}[ -]?\d{2}[ -]?\d{3}[ -]?[\dXx]\b',  # 身份证号（兼容空格/横线）
    r'\b(1[3-9]\d{1})[ -]?\d{4}[ -]?\d{4}\b',  # 手机号（兼容空格/横线）
    r'\b(张三|李四|王五)\b'  # 敏感姓名（示例）
]

# 黑名单应用窗口标题关键词
BLOCKED_APPS = ["微信", "wechat", "telegram", "skype", "whatsapp", "qq", "tim"]

# 黑名单应用进程名称
if IS_WINDOWS:
    BLOCKED_PROCESSES = ["WeChat.exe", "wechat.exe", "QQ.exe", "qq.exe", "TIM.exe", "tim.exe", "Telegram.exe", "telegram.exe"]
elif IS_MAC:
    BLOCKED_PROCESSES = ["WeChat", "wechat", "QQ", "Telegram", "TIM", "tim", "Skype", "WhatsApp"]

# 检测频率（秒）
CHECK_INTERVAL = 0.1

# 是否启用日志
ENABLE_LOG = True

# 日志文件路径
LOG_FILE = "safeclip_log.txt"

# ------------ 核心代码 ------------

# 全局变量
g_is_running = True
g_clipboard_content = ""
g_last_check_time = 0
g_is_sensitive = False

# Windows 特定的初始化
if IS_WINDOWS:
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    WM_CLIPBOARDUPDATE = 0x031D
    WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_int, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM)
    g_hwnd = None

def log_message(message):
    """记录日志"""
    if not ENABLE_LOG:
        return
        
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_entry = f"[{timestamp}] {message}\n"
    
    print(log_entry.strip())
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"写入日志失败: {str(e)}")

def get_clipboard_content():
    """获取剪贴板内容 - 使用多种方法"""
    content = ""
    
    # 方法1: 使用pyperclip (跨平台)
    try:
        content = pyperclip.paste()
        if content:
            return content
    except Exception as e:
        log_message(f"pyperclip获取剪贴板失败: {str(e)}")
    
    # 方法2: 平台特定方法
    if IS_WINDOWS:
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                content = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')
            elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                content = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except Exception as e:
            log_message(f"win32clipboard获取剪贴板失败: {str(e)}")
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
    elif IS_MAC:
        try:
            pasteboard = AppKit.NSPasteboard.generalPasteboard()
            content = pasteboard.stringForType_(AppKit.NSPasteboardTypeString)
        except Exception as e:
            log_message(f"Mac剪贴板获取失败: {str(e)}")
            
    return content

def is_clipboard_text_only():
    """检查剪贴板是否只包含文本内容"""
    if IS_WINDOWS:
        try:
            win32clipboard.OpenClipboard()
            
            # 检查是否有图片格式
            has_bitmap = win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_BITMAP)
            has_dib = win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB)
            has_dibv5 = win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIBV5)
            
            # 检查是否有文件格式
            has_hdrop = win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP)
            
            win32clipboard.CloseClipboard()
            
            # 如果存在图片或文件格式，则不是纯文本
            if has_bitmap or has_dib or has_dibv5 or has_hdrop:
                log_message("检测到剪贴板包含非文本内容（图片或文件）")
                return False
                
            return True
        except Exception as e:
            log_message(f"检查剪贴板格式失败: {str(e)}")
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return True  # 出错时默认为文本，更安全
    
    elif IS_MAC:
        try:
            pasteboard = AppKit.NSPasteboard.generalPasteboard()
            types = pasteboard.types()
            
            # 检查是否有图片类型
            has_image = AppKit.NSPasteboardTypeTIFF in types or AppKit.NSPasteboardTypePNG in types
            
            # 检查是否有文件类型
            has_file = AppKit.NSPasteboardTypeFileURL in types
            
            if has_image or has_file:
                log_message("检测到剪贴板包含非文本内容（图片或文件）")
                return False
                
            return True
        except Exception as e:
            log_message(f"Mac检查剪贴板格式失败: {str(e)}")
            return True  # 出错时默认为文本，更安全
    
    return True  # 默认为文本，更安全

def is_clipboard_has_image():
    """检查剪贴板是否包含图片内容"""
    if IS_WINDOWS:
        try:
            win32clipboard.OpenClipboard()
            
            # 检查是否有图片格式
            has_bitmap = win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_BITMAP)
            has_dib = win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB)
            has_dibv5 = win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIBV5)
            
            win32clipboard.CloseClipboard()
            
            # 如果存在图片格式，返回True
            if has_bitmap or has_dib or has_dibv5:
                log_message("检测到剪贴板包含图片内容")
                return True
                
            return False
        except Exception as e:
            log_message(f"检查剪贴板图片失败: {str(e)}")
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return False
    
    elif IS_MAC:
        try:
            pasteboard = AppKit.NSPasteboard.generalPasteboard()
            types = pasteboard.types()
            
            # 检查是否有图片类型
            has_image = AppKit.NSPasteboardTypeTIFF in types or AppKit.NSPasteboardTypePNG in types
            
            if has_image:
                log_message("检测到剪贴板包含图片内容")
                return True
                
            return False
        except Exception as e:
            log_message(f"Mac检查剪贴板图片失败: {str(e)}")
            return False
    
    return False

def clean_clipboard():
    """清空剪贴板"""
    if IS_WINDOWS:
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
            log_message("清空剪贴板")
        except Exception as e:
            log_message(f"清空剪贴板失败: {str(e)}")
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
    elif IS_MAC:
        try:
            pasteboard = AppKit.NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            log_message("清空剪贴板")
        except Exception as e:
            log_message(f"Mac清空剪贴板失败: {str(e)}")

def get_active_window_info():
    """获取当前活动窗口信息（标题和进程）"""
    title = ""
    process_name = ""
    
    if IS_WINDOWS:
        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                process_name = process.name()
            except Exception as e:
                log_message(f"获取窗口进程失败: {str(e)}")
        except Exception as e:
            log_message(f"获取窗口标题失败: {str(e)}")
    
    elif IS_MAC:
        try:
            # 获取当前活动窗口
            windows = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
                Quartz.kCGNullWindowID
            )
            
            for window in windows:
                if window.get('kCGWindowLayer', 0) == 0:  # 应用窗口通常在第0层
                    title = window.get('kCGWindowOwnerName', '')
                    if title:
                        # 尝试获取进程名称
                        app_name = window.get('kCGWindowOwnerName', '')
                        if app_name:
                            process_name = app_name
                            break
        except Exception as e:
            log_message(f"Mac获取窗口信息失败: {str(e)}")
    
    return title, process_name

def get_all_running_processes():
    """获取所有正在运行的进程名称"""
    try:
        return [p.name() for p in psutil.process_iter()]
    except Exception as e:
        log_message(f"获取进程列表失败: {str(e)}")
        return []

def is_blocked_app_active():
    """检测当前窗口是否在黑名单应用中"""
    # 获取当前窗口信息
    title, process_name = get_active_window_info()
    
    # 记录窗口信息
    log_message(f"当前窗口标题：{title}")
    if process_name:
        log_message(f"当前窗口进程：{process_name}")
    
    # 方法1: 通过窗口标题检测
    title_lower = title.lower()
    for app in BLOCKED_APPS:
        if app.lower() in title_lower:
            log_message(f"匹配到黑名单应用(标题): {app}")
            return True
    
    # 方法2: 通过进程名称检测
    if process_name and process_name in BLOCKED_PROCESSES:
        log_message(f"匹配到黑名单应用(进程): {process_name}")
        return True
    
    # 方法3: 检查所有运行的进程
    running_processes = get_all_running_processes()
    for proc in BLOCKED_PROCESSES:
        if proc in running_processes:
            log_message(f"检测到黑名单应用正在运行: {proc}")
            # 如果黑名单应用正在运行，并且窗口标题不明确，我们假设它可能是活动窗口
            if title == "" or len(title) < 3:
                log_message("窗口标题不明确，假设为黑名单应用")
                return True
    
    return False

def is_sensitive_content(text):
    """用正则检测敏感内容"""
    if not text or not isinstance(text, str):
        return False
        
    for pattern in SENSITIVE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            log_message(f"匹配到敏感内容: {match.group(0)}")
            return True
    return False

def show_message_box(title, message):
    """显示消息框"""
    if IS_WINDOWS:
        try:
            user32.MessageBoxW(None, message, title, 0)
        except Exception as e:
            log_message(f"显示消息框失败: {str(e)}")
    elif IS_MAC:
        try:
            script = f'display dialog "{message}" with title "{title}" buttons {{"确定"}} default button "确定"'
            subprocess.run(["osascript", "-e", script])
        except Exception as e:
            log_message(f"Mac显示消息框失败: {str(e)}")

def clipboard_monitor_thread():
    """剪贴板监控线程"""
    global g_clipboard_content, g_is_sensitive, g_last_check_time
    
    last_content = ""
    last_window_title = ""
    last_process_name = ""
    
    while g_is_running:
        try:
            # 控制检测频率
            current_time = time.time()
            if current_time - g_last_check_time < CHECK_INTERVAL:
                time.sleep(0.01)  # 短暂休眠，减少CPU使用
                continue
            g_last_check_time = current_time
            
            # 获取当前窗口信息
            current_title, current_process = get_active_window_info()
            
            # 检测窗口切换
            window_switched = (current_title != last_window_title or current_process != last_process_name)
            if window_switched:
                log_message(f"窗口切换: {last_window_title} -> {current_title}")
                log_message(f"进程切换: {last_process_name} -> {current_process}")
                
                # 如果切换到黑名单应用，立即检查剪贴板
                if is_blocked_app_active():
                    log_message("切换到黑名单应用，立即检查剪贴板")
                    current_content = get_clipboard_content()
                    
                    # 检查是否为敏感内容
                    if is_sensitive_content(current_content):
                        log_message(f"检测到敏感内容: {current_content[:50]}...")
                        clean_clipboard()
                        # 显示警告消息
                        threading.Thread(target=show_message_box, 
                                     args=("SafeClip 安全拦截", "检测到敏感内容，已清空剪贴板！")).start()
                    
                    # 检查是否包含图片
                    elif is_clipboard_has_image():
                        log_message("检测到图片内容，在黑名单应用中禁止粘贴图片")
                        clean_clipboard()
                        # 显示警告消息
                        threading.Thread(target=show_message_box, 
                                     args=("SafeClip 安全拦截", "在敏感应用中禁止粘贴图片！")).start()
                
                # 更新上一次窗口信息
                last_window_title = current_title
                last_process_name = current_process
            
            # 获取当前剪贴板内容
            current_content = get_clipboard_content()
            g_clipboard_content = current_content
            
            # 检查剪贴板内容是否变化
            if current_content != last_content:
                log_message(f"剪贴板内容变化: {current_content[:30]}..." if current_content else "剪贴板为空")
                
                # 检查是否为敏感内容
                if is_sensitive_content(current_content):
                    g_is_sensitive = True
                    log_message("检测到敏感内容")
                    
                    # 检查当前窗口是否在黑名单中
                    if is_blocked_app_active():
                        log_message("当前窗口在黑名单中")
                        log_message(f"拦截内容：{current_content[:50]}...")
                        
                        # 执行清空和提醒
                        clean_clipboard()
                        
                        # 在UI线程中显示消息框
                        threading.Thread(target=show_message_box, 
                                         args=("SafeClip 安全拦截", "检测到敏感内容，已阻止粘贴！")).start()
                else:
                    g_is_sensitive = False
                
                # 检查是否包含图片，且当前窗口在黑名单中
                if is_clipboard_has_image() and is_blocked_app_active():
                    log_message("检测到图片内容，在黑名单应用中禁止粘贴图片")
                    clean_clipboard()
                    # 显示警告消息
                    threading.Thread(target=show_message_box, 
                                     args=("SafeClip 安全拦截", "在敏感应用中禁止粘贴图片！")).start()
            
            # 更新上一次的剪贴板内容
            last_content = current_content
            
        except Exception as e:
            log_message(f"监控异常：{str(e)}")
            traceback.print_exc()
            time.sleep(1)

def aggressive_clipboard_cleaner_thread():
    """激进的剪贴板清理线程 - 定期检查并清空敏感内容"""
    global g_clipboard_content, g_is_sensitive
    
    while g_is_running:
        try:
            # 如果当前窗口在黑名单中
            if is_blocked_app_active():
                # 检查敏感内容
                if g_is_sensitive:
                    current_content = get_clipboard_content()
                    if is_sensitive_content(current_content):
                        log_message("激进清理: 检测到敏感内容仍在剪贴板中")
                        clean_clipboard()
                
                # 检查图片内容
                if is_clipboard_has_image():
                    log_message("激进清理: 检测到图片内容，在黑名单应用中禁止")
                    clean_clipboard()
            
            # 短暂休眠
            time.sleep(0.2)
            
        except Exception as e:
            log_message(f"激进清理异常：{str(e)}")
            time.sleep(1)

def keyboard_hook_thread():
    """模拟键盘钩子 - 定期检查并拦截粘贴操作"""
    global g_is_running
    
    if IS_WINDOWS:
        # Windows 键盘钩子
        # 检测Ctrl+V组合键的状态
        ctrl_state = 0
        v_state = 0
        
        while g_is_running:
            try:
                # 检测Ctrl键状态
                new_ctrl_state = win32api.GetAsyncKeyState(win32con.VK_CONTROL)
                
                # 检测V键状态
                new_v_state = win32api.GetAsyncKeyState(ord('V'))
                
                # 检测Ctrl+V组合
                if (new_ctrl_state & 0x8000) and (new_v_state & 0x8000) and not (ctrl_state & 0x8000) and not (v_state & 0x8000):
                    log_message("检测到Ctrl+V组合键")
                    
                    # 检查当前窗口是否在黑名单中
                    if is_blocked_app_active():
                        # 获取当前剪贴板内容
                        current_content = get_clipboard_content()
                        
                        # 检查是否为敏感内容
                        if is_sensitive_content(current_content):
                            log_message(f"拦截敏感内容粘贴: {current_content[:50]}...")
                            clean_clipboard()
                            
                            # 在UI线程中显示消息框
                            threading.Thread(target=show_message_box, 
                                             args=("SafeClip 安全拦截", "检测到敏感内容，已阻止粘贴！")).start()
                        
                        # 检查是否包含图片
                        elif is_clipboard_has_image():
                            log_message("拦截图片粘贴")
                            clean_clipboard()
                            
                            # 在UI线程中显示消息框
                            threading.Thread(target=show_message_box, 
                                             args=("SafeClip 安全拦截", "在敏感应用中禁止粘贴图片！")).start()
                
                # 更新按键状态
                ctrl_state = new_ctrl_state
                v_state = new_v_state
                
                # 短暂休眠
                time.sleep(0.01)
                
            except Exception as e:
                log_message(f"键盘钩子异常：{str(e)}")
                time.sleep(1)
    
    elif IS_MAC:
        # Mac 键盘钩子 - 使用 Mac 特定的方法
        log_message("Mac 键盘钩子启动")
        
        # 在 Mac 上，我们主要依赖剪贴板监控，因为 Mac 上的键盘钩子实现比较复杂
        # 这里只是一个占位，实际上我们依赖剪贴板监控和激进清理线程
        while g_is_running:
            time.sleep(1)

def main():
    """主函数"""
    global g_is_running, g_clipboard_content
    
    try:
        log_message(f"SafeClip 已启动，在{SYSTEM}系统上运行...")
        log_message("按Ctrl+C可退出程序")
        
        # 获取初始剪贴板内容
        g_clipboard_content = get_clipboard_content()
        log_message(f"初始剪贴板内容: {g_clipboard_content[:30]}..." if g_clipboard_content else "剪贴板为空")
        
        # 启动剪贴板监控线程
        monitor_thread = threading.Thread(target=clipboard_monitor_thread)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 启动激进的剪贴板清理线程
        cleaner_thread = threading.Thread(target=aggressive_clipboard_cleaner_thread)
        cleaner_thread.daemon = True
        cleaner_thread.start()
        
        # 启动键盘钩子线程
        keyboard_thread = threading.Thread(target=keyboard_hook_thread)
        keyboard_thread.daemon = True
        keyboard_thread.start()
        
        # 主线程等待用户中断
        while g_is_running:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        log_message("用户中断，程序即将退出...")
        g_is_running = False
    except Exception as e:
        log_message(f"程序异常: {str(e)}")
        traceback.print_exc()
    finally:
        g_is_running = False
        log_message("程序已退出")

if __name__ == "__main__":
    try:
        # 检查操作系统并安装必要的依赖
        if IS_WINDOWS:
            # Windows 依赖已在顶部导入
            pass
        elif IS_MAC:
            # Mac 依赖已在顶部导入
            pass
        else:
            log_message(f"不支持的操作系统: {SYSTEM}")
            sys.exit(1)
            
        main()
    except Exception as e:
        log_message(f"程序启动异常: {str(e)}")
        traceback.print_exc()
        input("按Enter键退出...")