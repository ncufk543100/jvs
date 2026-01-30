/**
 * 贾维斯2号文件系统权限守卫
 * 确保只能在指定的工作区内修改文件
 */

import * as fs from 'fs';
import * as path from 'path';

// 配置
const WRITABLE_ZONE = 'D:\\jarvisbox';
const VIOLATION_LOG = path.join(WRITABLE_ZONE, 'logs', 'permission_violations.log');

/**
 * 规范化路径（处理Windows/Unix路径差异）
 */
function normalizePath(filePath: string): string {
  return path.normalize(filePath).toLowerCase();
}

/**
 * 检查路径是否在可写区域内
 */
export function isInWritableZone(filePath: string): boolean {
  const normalized = normalizePath(filePath);
  const writableZone = normalizePath(WRITABLE_ZONE);
  
  // 检查是否以可写区域开头
  return normalized.startsWith(writableZone);
}

/**
 * 检查文件操作权限
 */
export function checkFilePermission(
  operation: 'read' | 'write' | 'delete' | 'create',
  filePath: string
): { allowed: boolean; reason?: string } {
  // 读操作始终允许
  if (operation === 'read') {
    return { allowed: true };
  }

  // 写/删除/创建操作需要在可写区域内
  if (!isInWritableZone(filePath)) {
    return {
      allowed: false,
      reason: `文件 "${filePath}" 不在可写区域内。只能修改 ${WRITABLE_ZONE} 目录下的文件。`
    };
  }

  return { allowed: true };
}

/**
 * 记录权限违规
 */
function logViolation(operation: string, filePath: string, reason: string): void {
  const timestamp = new Date().toISOString();
  const logEntry = `[${timestamp}] VIOLATION: ${operation} on "${filePath}" - ${reason}\n`;
  
  try {
    // 确保日志目录存在
    const logDir = path.dirname(VIOLATION_LOG);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    
    fs.appendFileSync(VIOLATION_LOG, logEntry);
  } catch (error) {
    console.error('Failed to log violation:', error);
  }
}

/**
 * 安全的文件写入
 */
export async function safeWriteFile(
  filePath: string,
  content: string | Buffer
): Promise<{ success: boolean; error?: string }> {
  const permission = checkFilePermission('write', filePath);
  
  if (!permission.allowed) {
    logViolation('WRITE', filePath, permission.reason!);
    return {
      success: false,
      error: permission.reason
    };
  }

  try {
    // 确保目录存在
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    fs.writeFileSync(filePath, content);
    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: `写入失败: ${error}`
    };
  }
}

/**
 * 安全的文件删除
 */
export async function safeDeleteFile(
  filePath: string
): Promise<{ success: boolean; error?: string }> {
  const permission = checkFilePermission('delete', filePath);
  
  if (!permission.allowed) {
    logViolation('DELETE', filePath, permission.reason!);
    return {
      success: false,
      error: permission.reason
    };
  }

  try {
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: `删除失败: ${error}`
    };
  }
}

/**
 * 复制文件到可写区域
 */
export async function copyToWritableZone(
  sourcePath: string,
  targetName?: string
): Promise<{ success: boolean; targetPath?: string; error?: string }> {
  try {
    // 读取源文件
    if (!fs.existsSync(sourcePath)) {
      return {
        success: false,
        error: `源文件不存在: ${sourcePath}`
      };
    }

    // 确定目标路径
    const fileName = targetName || path.basename(sourcePath);
    const targetPath = path.join(WRITABLE_ZONE, 'imported', fileName);

    // 确保目标目录存在
    const targetDir = path.dirname(targetPath);
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    // 复制文件
    fs.copyFileSync(sourcePath, targetPath);

    return {
      success: true,
      targetPath
    };
  } catch (error) {
    return {
      success: false,
      error: `复制失败: ${error}`
    };
  }
}

/**
 * 获取建议的操作
 */
export function getSuggestion(operation: string, filePath: string): string {
  if (isInWritableZone(filePath)) {
    return `可以直接${operation}文件: ${filePath}`;
  }

  return `无法直接${operation}文件 "${filePath}"。\n建议：\n1. 使用 copyToWritableZone() 将文件复制到 ${WRITABLE_ZONE}\n2. 在复制后的文件上进行修改`;
}
