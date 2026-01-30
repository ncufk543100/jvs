/**
 * 文件系统权限守卫测试
 */

import {
  isInWritableZone,
  checkFilePermission,
  safeWriteFile,
  safeDeleteFile,
  copyToWritableZone,
  getSuggestion
} from './filesystem-guard';

// 测试用例
const testCases = {
  writableZone: [
    'D:\\jarvisbox\\test.txt',
    'D:\\jarvisbox\\subfolder\\file.txt',
    'D:\\JARVISBOX\\UPPERCASE.TXT', // 大小写不敏感
  ],
  readonlyZone: [
    'C:\\Windows\\system32\\config.ini',
    'C:\\Users\\Documents\\file.txt',
    'D:\\other\\file.txt',
  ]
};

console.log('=== 文件系统权限守卫测试 ===\n');

// 测试1: 检查路径是否在可写区域
console.log('测试1: 检查路径是否在可写区域');
testCases.writableZone.forEach(path => {
  const result = isInWritableZone(path);
  console.log(`  ${path}: ${result ? '✅ 可写' : '❌ 只读'}`);
});

testCases.readonlyZone.forEach(path => {
  const result = isInWritableZone(path);
  console.log(`  ${path}: ${result ? '✅ 可写' : '❌ 只读'}`);
});

console.log('\n测试2: 检查文件操作权限');

// 测试2a: 读操作（应该都允许）
console.log('  2a. 读操作（应该都允许）:');
[...testCases.writableZone, ...testCases.readonlyZone].forEach(path => {
  const result = checkFilePermission('read', path);
  console.log(`    ${path}: ${result.allowed ? '✅ 允许' : '❌ 拒绝'}`);
});

// 测试2b: 写操作（只允许可写区域）
console.log('  2b. 写操作（只允许可写区域）:');
testCases.writableZone.forEach(path => {
  const result = checkFilePermission('write', path);
  console.log(`    ${path}: ${result.allowed ? '✅ 允许' : '❌ 拒绝'}`);
});

testCases.readonlyZone.forEach(path => {
  const result = checkFilePermission('write', path);
  console.log(`    ${path}: ${result.allowed ? '✅ 允许' : `❌ 拒绝 - ${result.reason}`}`);
});

// 测试3: 获取建议
console.log('\n测试3: 获取操作建议');
console.log('  可写区域文件:');
console.log(`    ${getSuggestion('修改', testCases.writableZone[0])}`);
console.log('  只读区域文件:');
console.log(`    ${getSuggestion('修改', testCases.readonlyZone[0])}`);

console.log('\n=== 测试完成 ===');
console.log('\n注意: 实际的文件操作测试需要在真实环境中运行');
console.log('      (需要D:\\jarvisbox目录存在)');
