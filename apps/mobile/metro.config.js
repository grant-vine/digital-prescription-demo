const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const projectRoot = __dirname;
const workspaceRoot = path.resolve(projectRoot, '../..');

const config = getDefaultConfig(projectRoot);

config.watchFolders = [workspaceRoot];
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
  path.resolve(workspaceRoot, 'node_modules'),
];

config.resolver.blockList = [
  /.*\.test\.[jt]sx?$/,
  /.*\.spec\.[jt]sx?$/,
  /.*\/__tests__\/.*/,
  /.*\/e2e\/.*/,
];

module.exports = config;
