#!/bin/bash
# 贾维斯自动化工具链：版本控制与 GitHub 同步脚本

VERSION_FILE="../huozhe-taro/package.json"
README_FILE="../huozhe-taro/README.md"

function increment_version() {
    # 肆爷定义的百进制版本规则：x.yy.zz
    # 当前版本格式示例: 1.55.16
    current_version=$(grep '"version":' $VERSION_FILE | sed -E 's/.*"([^"]+)".*/\1/')
    IFS='.' read -r major minor patch <<< "$current_version"
    
    # 每次增加 0.00.01
    new_patch=$((patch + 1))
    if [ $new_patch -gt 99 ]; then
        new_patch=0
        minor=$((minor + 1))
    fi
    
    new_version="$major.$minor.$(printf "%02d" $new_patch)"
    echo "贾维斯：正在从 v$current_version 升级至 v$new_version"
    
    # 更新文件
    sed -i "s/\"version\": \"$current_version\"/\"version\": \"$new_version\"/" $VERSION_FILE
}

function sync_to_github() {
    commit_msg=$1
    git add .
    git commit -m "jarvis(auto): $commit_msg"
    git push origin main
    echo "贾维斯：已同步至 GitHub main 分支"
}

# 示例调用
# increment_version
# sync_to_github "update core logic"
