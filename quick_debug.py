#!/usr/bin/env python3
"""
快速调试PDF检测逻辑
"""
import os
from modules.caj_converter import CAJConverter

def test_detection():
    # 先找到实际存在的CAJ文件
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        print("❌ uploads目录不存在")
        return
    
    caj_files = [f for f in os.listdir(uploads_dir) if f.lower().endswith('.caj')]
    if not caj_files:
        print("❌ 没有找到CAJ文件")
        return
    
    test_file = os.path.join(uploads_dir, caj_files[0])
    print(f"🔍 找到测试文件: {test_file}")
    print(f"文件是否存在: {os.path.exists(test_file)}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"文件绝对路径: {os.path.abspath(test_file)}")
    
    # 手动检查文件头（不切换工作目录）
    print("\n📋 直接检查文件头:")
    try:
        with open(test_file, 'rb') as f:
            header = f.read(8)
            print(f"文件头: {header}")
            print(f"是否以%PDF开头: {header.startswith(b'%PDF')}")
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return
    
    # 测试不使用上下文管理器的检测方法
    print("\n🔧 不使用上下文管理器测试:")
    converter = CAJConverter()
    
    print("测试 is_caj_file():")
    result1 = converter.is_caj_file(test_file)
    print(f"  结果: {result1}")
    
    print("测试 is_pdf_disguised_as_caj():")
    result2 = converter.is_pdf_disguised_as_caj(test_file)
    print(f"  结果: {result2}")
    
    print(f"条件检查: not {result1} and not {result2} = {not result1 and not result2}")
    
    # 测试使用上下文管理器
    print("\n🔧 使用上下文管理器测试:")
    try:
        with CAJConverter() as converter_ctx:
            print(f"切换后工作目录: {os.getcwd()}")
            print(f"文件是否存在: {os.path.exists(test_file)}")
            print(f"绝对路径是否存在: {os.path.exists(os.path.abspath(test_file))}")
            
            result3 = converter_ctx.is_caj_file(test_file)
            print(f"上下文中 is_caj_file(): {result3}")
            
            result4 = converter_ctx.is_pdf_disguised_as_caj(test_file)
            print(f"上下文中 is_pdf_disguised_as_caj(): {result4}")
    except Exception as e:
        print(f"❌ 上下文测试失败: {e}")

if __name__ == "__main__":
    test_detection() 