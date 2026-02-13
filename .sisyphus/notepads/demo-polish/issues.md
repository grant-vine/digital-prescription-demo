# Demo Polish - Issues & Gotchas

This notepad tracks problems and gotchas encountered during the demo polish project.

---

## Known Issues (2026-02-13)

### No Critical Blockers
All environment checks passed. No blocking issues identified.

### Phase 6 Work Items (Camera Handling)
1. **Camera fallback needed**: If `expo-camera` CameraView unavailable at runtime
   - Files affected: QRScanner.tsx, scan.tsx, verify.tsx
   - Solution: Mock camera component or qrcode input fallback
   - Status: Not blocking demo (QR manual entry can be used)

2. **Expo Web camera limitation**: Web platform cannot access native camera
   - Workaround: Implement file upload or manual entry for web builds
   - Priority: Medium (Web is secondary to mobile)

### Configuration Notes
- Backend uses SQLite for dev (not PostgreSQL)
- No explicit DEMO_MODE env var set (will need to be added to .env for scripts)
- Expo Web not currently running (need `npx expo start` from apps/mobile/)

