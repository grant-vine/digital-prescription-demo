// Local entry point that re-exports expo-router/entry
// This avoids Metro's inability to resolve hoisted workspace dependencies
// as entry points (the "main" field resolution doesn't use nodeModulesPaths)
require("expo-router/entry");
