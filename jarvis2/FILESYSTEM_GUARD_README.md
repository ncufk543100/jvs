# 文件系统权限守卫

## 概述

贾维斯2号的文件系统权限守卫确保AI只能在指定的工作区内修改文件，保护系统其他区域的安全。

## 权限规则

### 可写区域
- **路径**: `D:\jarvisbox`
- **权限**: 读、写、删除、创建
- **说明**: 贾维斯2号的专属工作区

### 只读区域
- **路径**: 系统其他所有区域
- **权限**: 仅读取
- **说明**: 可以读取和使用，但不能修改

## 修改规则

如需修改只读区域的文件，必须遵循以下流程：

1. **检测目标文件路径**
2. **如果在只读区域**：拒绝直接修改
3. **提示用户**：需要先复制到 `D:\jarvisbox`
4. **提供自动复制选项**

## API使用

### 检查权限

```typescript
import { checkFilePermission } from './src/filesystem-guard';

const result = checkFilePermission('write', 'C:\\Users\\file.txt');
if (!result.allowed) {
  console.log(result.reason);
}
```

### 安全写入

```typescript
import { safeWriteFile } from './src/filesystem-guard';

const result = await safeWriteFile('D:\\jarvisbox\\output.txt', 'content');
if (!result.success) {
  console.error(result.error);
}
```

### 复制到可写区域

```typescript
import { copyToWritableZone } from './src/filesystem-guard';

const result = await copyToWritableZone('C:\\source\\file.txt');
if (result.success) {
  console.log(`已复制到: ${result.targetPath}`);
  // 现在可以修改复制后的文件
}
```

### 获取建议

```typescript
import { getSuggestion } from './src/filesystem-guard';

const suggestion = getSuggestion('修改', 'C:\\Users\\file.txt');
console.log(suggestion);
```

## 违规日志

所有权限违规尝试都会记录到：
```
D:\jarvisbox\logs\permission_violations.log
```

日志格式：
```
[2026-01-30T12:34:56.789Z] VIOLATION: WRITE on "C:\Users\file.txt" - 文件不在可写区域内
```

## 配置

权限配置存储在 `FILESYSTEM_PERMISSIONS.json`:

```json
{
  "rules": {
    "writable_zones": [
      {
        "path": "D:\\jarvisbox",
        "permissions": ["read", "write", "delete", "create"]
      }
    ]
  },
  "enforcement": {
    "enabled": true,
    "strict_mode": true,
    "log_violations": true
  }
}
```

## 安全特性

1. **严格模式**: 默认启用，拒绝所有未授权的写操作
2. **违规日志**: 记录所有违规尝试，便于审计
3. **自动提示**: 当尝试修改只读文件时，自动提供解决方案
4. **路径规范化**: 处理Windows/Unix路径差异，防止绕过

## 最佳实践

1. **始终使用安全API**: 使用 `safeWriteFile` 而不是直接的 `fs.writeFile`
2. **检查权限**: 在操作前使用 `checkFilePermission` 检查
3. **复制后修改**: 对只读文件，先复制到工作区再修改
4. **定期审计**: 检查违规日志，发现潜在问题

## 示例工作流

### 修改系统文件

```typescript
// 错误方式（会被拒绝）
await safeWriteFile('C:\\Windows\\system32\\config.ini', 'new content');
// ❌ 失败: 文件不在可写区域内

// 正确方式
const copyResult = await copyToWritableZone('C:\\Windows\\system32\\config.ini');
if (copyResult.success) {
  await safeWriteFile(copyResult.targetPath!, 'new content');
  // ✅ 成功: 在工作区内修改
}
```

### 读取任意文件

```typescript
// 读取始终允许
const content = fs.readFileSync('C:\\Users\\Documents\\file.txt', 'utf8');
// ✅ 成功: 读操作不受限制
```

## 版本历史

- **v1.0.1** (2026-01-30): 初始版本，实现基础权限控制
