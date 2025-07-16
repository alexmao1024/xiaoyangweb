"""
主页路由模块
处理首页和工具箱导航相关的路由
"""

from flask import Blueprint, render_template

# 创建蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """渲染首页 - 小羊的工具箱"""
    return render_template('index.html') 