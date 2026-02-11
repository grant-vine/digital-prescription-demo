/* Structure validation tests for mobile app. */

import fs from 'fs';

describe('Mobile App Structure', () => {
  describe('Directory Structure', () => {
    test('should have required source directories', () => {
      const requiredDirs = [
        'apps/mobile/src/app',
        'apps/mobile/src/components',
        'apps/mobile/src/hooks',
        'apps/mobile/src/services',
        'apps/mobile/src/store',
      ];

      requiredDirs.forEach((dir) => {
        expect(fs.existsSync(dir)).toBe(true);
      });
    });

    test('should have tests directory', () => {
      expect(fs.existsSync('apps/mobile/src/tests')).toBe(true);
    });
  });

  describe('Package Configuration', () => {
    test('should have valid package.json with required scripts', () => {
      const packageJsonPath = 'apps/mobile/package.json';
      expect(fs.existsSync(packageJsonPath)).toBe(true);

      const packageJson = JSON.parse(
        fs.readFileSync(packageJsonPath, 'utf-8')
      );
      const requiredScripts = ['start', 'test', 'lint', 'type-check'];

      requiredScripts.forEach((script) => {
        expect(packageJson.scripts).toHaveProperty(script);
      });
    });

    test('should have package.json with valid structure', () => {
      const packageJson = JSON.parse(
        fs.readFileSync('apps/mobile/package.json', 'utf-8')
      );

      expect(packageJson.name).toBeDefined();
      expect(packageJson.version).toBeDefined();
      expect(packageJson.scripts).toBeDefined();
      expect(typeof packageJson.scripts).toBe('object');
    });
  });

  describe('Configuration Files', () => {
    test('should have jest.config.js', () => {
      expect(fs.existsSync('apps/mobile/jest.config.js')).toBe(true);
    });

    test('should have tsconfig.json', () => {
      expect(fs.existsSync('apps/mobile/tsconfig.json')).toBe(true);
    });

    test('should have .eslintrc or eslint config', () => {
      const eslintFiles = [
        'apps/mobile/.eslintrc',
        'apps/mobile/.eslintrc.js',
        'apps/mobile/.eslintrc.json',
      ];

      const hasEslint = eslintFiles.some((file) =>
        fs.existsSync(file)
      );

      expect(hasEslint || JSON.parse(
        fs.readFileSync('apps/mobile/package.json', 'utf-8')
      ).eslintConfig).toBeTruthy();
    });
  });
});
