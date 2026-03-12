"""
测试报告模板

生成 HTML 测试报告
"""
import os
from datetime import datetime

# 报告模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试用例生成平台 - 测试报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px 8px 0 0;
        }}
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            opacity: 0.9;
            font-size: 14px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            padding: 30px;
            border-bottom: 1px solid #eee;
        }}
        .stat-card {{
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            background: #f8f9fa;
        }}
        .stat-card.total {{ background: #e3f2fd; }}
        .stat-card.passed {{ background: #e8f5e9; }}
        .stat-card.failed {{ background: #ffebee; }}
        .stat-card.skip {{ background: #fff3e0; }}
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            display: block;
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
        .stat-card.total .stat-value {{ color: #1976d2; }}
        .stat-card.passed .stat-value {{ color: #388e3c; }}
        .stat-card.failed .stat-value {{ color: #d32f2f; }}
        .stat-card.skip .stat-value {{ color: #f57c00; }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        .test-list {{
            list-style: none;
        }}
        .test-item {{
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 6px;
            background: #f8f9fa;
            border-left: 4px solid #ccc;
        }}
        .test-item.passed {{ border-left-color: #4caf50; }}
        .test-item.failed {{ border-left-color: #f44336; }}
        .test-item.skipped {{ border-left-color: #ff9800; }}
        .test-name {{
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }}
        .test-duration {{
            font-size: 12px;
            color: #999;
        }}
        .test-message {{
            font-size: 13px;
            color: #666;
            margin-top: 8px;
            padding: 8px;
            background: white;
            border-radius: 4px;
        }}
        .footer {{
            padding: 20px 30px;
            text-align: center;
            color: #999;
            font-size: 13px;
            border-top: 1px solid #eee;
        }}
        .progress-bar {{
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 测试用例生成平台 - 测试报告</h1>
            <div class="subtitle">
                执行时间: {exec_time} | 环境: {environment}
            </div>
        </div>
        
        <div class="summary">
            <div class="stat-card total">
                <span class="stat-value">{total}</span>
                <span class="stat-label">总测试数</span>
            </div>
            <div class="stat-card passed">
                <span class="stat-value">{passed}</span>
                <span class="stat-label">通过</span>
            </div>
            <div class="stat-card failed">
                <span class="stat-value">{failed}</span>
                <span class="stat-label">失败</span>
            </div>
            <div class="stat-card skip">
                <span class="stat-value">{skipped}</span>
                <span class="stat-label">跳过</span>
            </div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2 class="section-title">📋 测试模块概览</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f5f7fa;">
                            <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">模块</th>
                            <th style="padding: 12px; text-align: center; border-bottom: 2px solid #ddd;">总数</th>
                            <th style="padding: 12px; text-align: center; border-bottom: 2px solid #ddd;">通过</th>
                            <th style="padding: 12px; text-align: center; border-bottom: 2px solid #ddd;">失败</th>
                            <th style="padding: 12px; text-align: center; border-bottom: 2px solid #ddd;">通过率</th>
                        </tr>
                    </thead>
                    <tbody>
                        {module_table}
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2 class="section-title">❌ 失败测试详情</h2>
                {failed_tests}
            </div>
        </div>
        
        <div class="footer">
            <p>测试用例生成平台 - 自动化测试报告</p>
            <p>Generated by pytest + custom HTML template</p>
        </div>
    </div>
</body>
</html>
"""


def generate_report(
    total: int = 0,
    passed: int = 0,
    failed: int = 0,
    skipped: int = 0,
    modules: dict = None,
    failed_tests: list = None,
    output_path: str = "test_report.html"
):
    """生成 HTML 测试报告"""
    
    if modules is None:
        modules = {}
    
    if failed_tests is None:
        failed_tests = []
    
    # 生成模块表格
    module_rows = ""
    for module_name, stats in modules.items():
        pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        module_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #eee;">{module_name}</td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #eee;">{stats['total']}</td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #eee; color: #4caf50;">{stats['passed']}</td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #eee; color: #f44336;">{stats['failed']}</td>
            <td style="padding: 12px; text-align: center; border-bottom: 1px solid #eee;">{pass_rate:.1f}%</td>
        </tr>
        """
    
    # 生成失败测试详情
    if failed_tests:
        failed_html = '<ul class="test-list">'
        for test in failed_tests:
            failed_html += f"""
            <li class="test-item failed">
                <div class="test-name">🔴 {test['name']}</div>
                <div class="test-duration">耗时: {test.get('duration', 'N/A')}</div>
                <div class="test-message">{test.get('message', '')}</div>
            </li>
            """
        failed_html += '</ul>'
    else:
        failed_html = '<p style="color: #4caf50; padding: 20px;">🎉 所有测试通过！</p>'
    
    # 填充模板
    report = HTML_TEMPLATE.format(
        exec_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        environment="Test Environment",
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        module_table=module_rows,
        failed_tests=failed_html
    )
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return output_path


def generate_summary_report(test_results: list) -> dict:
    """从测试结果生成汇总"""
    
    summary = {
        "total": len(test_results),
        "passed": sum(1 for r in test_results if r.get("status") == "passed"),
        "failed": sum(1 for r in test_results if r.get("status") == "failed"),
        "skipped": sum(1 for r in test_results if r.get("status") == "skipped"),
    }
    
    return summary


if __name__ == "__main__":
    # 示例使用
    generate_report(
        total=50,
        passed=45,
        failed=3,
        skipped=2,
        modules={
            "用户管理": {"total": 15, "passed": 14, "failed": 1},
            "系统模块": {"total": 12, "passed": 12, "failed": 0},
            "用例生成": {"total": 15, "passed": 13, "failed": 2},
            "LLM集成": {"total": 8, "passed": 6, "failed": 0},
        },
        failed_tests=[
            {"name": "test_register_duplicate_username", "duration": "0.12s", "message": "User already exists"},
            {"name": "test_generate_with_empty_text", "duration": "0.08s", "message": "Empty input not handled"},
        ]
    )
    print("Report generated: test_report.html")
