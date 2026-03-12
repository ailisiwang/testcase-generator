#!/bin/bash
# 测试运行脚本

set -e

echo "========================================"
echo "测试用例生成平台 - 测试运行"
echo "========================================"

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "建议在虚拟环境中运行..."
fi

# 安装测试依赖
echo "安装测试依赖..."
pip install -r tests/requirements-test.txt --quiet

# 运行测试
echo ""
echo "开始运行测试..."
echo "----------------------------------------"

cd "$(dirname "$0")"

# 运行所有测试
python -m pytest tests/ \
    -v \
    --tb=short \
    --strict-markers \
    -p no:cacheprovider \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing

echo ""
echo "----------------------------------------"
echo "测试完成！"
echo ""

# 生成报告
if [ -f "test_report.html" ]; then
    echo "报告已生成: test_report.html"
fi
