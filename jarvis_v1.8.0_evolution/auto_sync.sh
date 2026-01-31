#!/bin/bash
# 贾维斯自动化版本管理与 GitHub 同步脚本
# 严格执行：每改必同步，即时更新版本号

set -e

VERSION_FILE="VERSION.json"
README_FILE="README.md"

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取当前版本
get_current_version() {
    grep '"version":' $VERSION_FILE | sed -E 's/.*"([^"]+)".*/\1/'
}

# 增加版本号（百进制规则）
increment_version() {
    current_version=$(get_current_version)
    IFS='.' read -r major minor patch <<< "$current_version"
    
    # 每次增加 0.0.1
    new_patch=$((patch + 1))
    
    # 百进制进位规则
    if [ $new_patch -gt 99 ]; then
        new_patch=0
        minor=$((minor + 1))
    fi
    
    if [ $minor -gt 9 ]; then
        echo -e "${YELLOW}警告：次版本号已达到上限 9，需要手动调整主版本号${NC}"
        exit 1
    fi
    
    new_version="$major.$minor.$new_patch"
    echo -e "${BLUE}贾维斯：版本升级 v$current_version → v$new_version${NC}"
    
    # 更新 VERSION.json
    sed -i "s/\"version\": \"$current_version\"/\"version\": \"$new_version\"/" $VERSION_FILE
    
    # 更新 README.md 中的版本号
    sed -i "s/v$current_version/v$new_version/g" $README_FILE
    
    echo "$new_version"
}

# 同步到 GitHub
sync_to_github() {
    commit_msg=$1
    new_version=$2
    
    echo -e "${BLUE}贾维斯：准备同步到 GitHub...${NC}"
    
    # 添加所有更改
    git add .
    
    # 提交更改
    git commit -m "jarvis(v$new_version): $commit_msg"
    
    # 推送到 main 分支
    git push origin main
    
    echo -e "${GREEN}✓ 贾维斯：已成功同步至 GitHub main 分支${NC}"
}

# 主流程
main() {
    if [ $# -eq 0 ]; then
        echo "用法: ./auto_sync.sh \"提交说明\""
        echo "示例: ./auto_sync.sh \"添加新功能：家庭伦理分析\""
        exit 1
    fi
    
    commit_message=$1
    
    # 检查是否有更改
    if [ -z "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}没有需要提交的更改${NC}"
        exit 0
    fi
    
    # 增加版本号
    new_version=$(increment_version)
    
    # 同步到 GitHub
    sync_to_github "$commit_message" "$new_version"
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}贾维斯同步完成！${NC}"
    echo -e "${GREEN}版本: v$new_version${NC}"
    echo -e "${GREEN}说明: $commit_message${NC}"
    echo -e "${GREEN}========================================${NC}"
}

main "$@"
