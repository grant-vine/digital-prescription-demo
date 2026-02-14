# Investor Demo Guide

## Overview
Complete walkthrough of the Digital Prescription Demo for investors.

## Flow
1. [Doctor creates prescription](#doctor-flow)
2. [Patient receives prescription](#patient-flow)
3. [Pharmacist verifies and dispenses](#pharmacist-flow)

## Talking Points
### Value Proposition
- Self-Sovereign Identity (SSI) - patient owns their data
- Cryptographic signatures - tamper-proof prescriptions
- Full audit trail - compliance ready

### Technical Highlights
- W3C Verifiable Credentials standard
- Blockchain-based DIDs
- QR code handoff (no app download required)

## FAQ
See full FAQ in demo presentation.

## Platform Support

### Demo Environment
**Optimized for:** Desktop browsers (Chrome 90+, Firefox 88+, Safari 14+)

**Supported:**
- ✅ Chrome 90+ (Recommended for best performance)
- ✅ Firefox 88+
- ✅ Safari 14+ (Camera requires HTTPS)
- ✅ Edge 90+

**Limited Support:**
- ⚠️ Mobile browsers (iOS Safari, Android Chrome) - Camera access requires HTTPS
- ⚠️ Tablet browsers - Touch interactions may differ

**Not Supported:**
- ❌ Internet Explorer
- ❌ Chrome < 80

### Why Desktop for Investor Demos?

This demo uses **Expo Web**, which optimizes for rapid development and investor presentations. The web build provides:

- ✅ Instant access (no app store downloads)
- ✅ Cross-platform (works on any device with browser)
- ✅ Easy updates (deploy new version instantly)
- ✅ Video recording (Playwright automation)

**For Production:**
Native iOS and Android apps are planned with full camera integration, biometric authentication, and offline support. The web demo showcases the core SSI (Self-Sovereign Identity) technology that powers both web and native experiences.

### Demo Fallbacks

If camera access fails during demo:
1. **QR Scanning** - Use "Copy as Text" button to manually transfer data
2. **Network Issues** - Demo works offline after initial load (except verification)
3. **Browser Issues** - Chrome is the recommended fallback

### Investor Questions

**Q: Can I try this on my phone?**
A: Yes, but we recommend desktop for the best experience. The mobile browser version works but has limited camera support due to HTTPS requirements for camera access in mobile browsers.

**Q: Is this the final app?**
A: This is a web demo showcasing the core technology. Production will include native iOS/Android apps with enhanced features like biometric authentication, offline storage, and optimized performance for mobile devices.

**Q: What about offline support?**
A: Patients can view prescriptions offline after they're received. Issuance and verification require internet connectivity for cryptographic signature validation.

**Q: Why not use the native app right now?**
A: The web demo provides instant deployment for investor presentations without app store downloads. This accelerates feedback loops. Native apps will follow, leveraging the same SSI backend infrastructure with enhanced mobile features.

**Q: What about security?**
A: All prescriptions are cryptographically signed using DIDs (Decentralized Identifiers) and W3C Verifiable Credentials. Each prescription includes tamper-proof signatures and a complete audit trail for compliance.

**Q: How scalable is this?**
A: The backend uses FastAPI with PostgreSQL and Redis, deployed on Kubernetes for production. The demo is optimized for MacBook Air 8GB; production scales to enterprise volume.

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| **Doctor** | `sarah.johnson@hospital.co.za` | `Demo@2024` |
| **Patient** | `john.smith@example.com` | `Demo@2024` |
| **Pharmacist** | `lisa.chen@pharmacy.co.za` | `Demo@2024` |

## Getting Started

### Quick Start
```bash
./scripts/start-demo.sh
```

This single command:
- ✅ Checks prerequisites (Python 3.12+, Node.js 20+, Docker)
- ✅ Starts Docker infrastructure (PostgreSQL, Redis, ACA-Py)
- ✅ Seeds demo data
- ✅ Launches backend API (http://localhost:8000)
- ✅ Launches mobile app (http://localhost:8081)
- ✅ Displays demo credentials

**First run: 3-5 minutes** (downloading Docker images)  
**Subsequent runs: <1 minute**

### Accessing the Demo

**Mobile App:**
- Browser: http://localhost:8081
- Or scan Expo QR code with your phone (desktop recommended)

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health

## Demo Flow (5-7 minutes)

### 1. Doctor Flow (2 min)
1. Login as doctor with credentials above
2. Click "Create Prescription"
3. Fill in patient name (John Smith)
4. Add medication details
5. Click "Sign & Issue"
6. Show QR code containing signed prescription

### 2. Patient Flow (2 min)
1. Login as patient with credentials above
2. Click "Scan Prescription" or paste QR code text
3. View received prescription in wallet
4. Show prescription details (medication, dosage, instructions)
5. Click "Share with Pharmacist" to generate share QR code

### 3. Pharmacist Flow (2 min)
1. Login as pharmacist with credentials above
2. Click "Verify Prescription"
3. Scan patient's share QR code
4. View prescription verification status (✅ Valid)
5. Click "Dispense Medication"
6. Show audit trail entry

## Video Demo

A professional 3-panel demo video is available: `demo-investor-final.mp4`
- Duration: 17.7 seconds
- Format: Side-by-side (Doctor, Patient, Pharmacist)
- Ready to share with investors

## Technical Stack (Talking Points)

**Mobile:** React Native + Expo (cross-platform, no app store)
**Backend:** FastAPI + Python (fast, modern)
**Database:** PostgreSQL (reliable)
**SSI:** ACA-Py or DIDx (blockchain-based identity)
**Infrastructure:** Docker Compose (dev) / Kubernetes (production)

## Production Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| MVP | 4 weeks | Web demo with ACA-Py |
| Migration | 2 weeks | DIDx CloudAPI integration |
| Enhanced | 4 weeks | FHIR, DIDComm, repeats |
| Production | 4 weeks | Native apps, K8s, monitoring |
| **Total** | **14 weeks** | Production-ready system |

## Talking Points Summary

### Problem Solved
- Paper prescriptions are inefficient and insecure
- Digital prescriptions lack patient control
- No tamper-proof verification

### Our Solution
- Patient-owned prescriptions (SSI)
- Cryptographically signed (tamper-proof)
- Instant verification (zero trust required)

### Key Differentiator
- QR code handoff (simple, no app required)
- Built on W3C standards (industry-standard)
- Blockchain-based identity (permanent, decentralized)

### Market Opportunity
- Healthcare digitalization trend
- Regulatory push (compliance requirements)
- Prescription volume (millions per year)
- Multi-tenancy (hospitals, clinics, pharmacies)

## Troubleshooting

### Port conflicts
```bash
# Kill process on port 8000 or 8081
lsof -ti:8000 | xargs kill
lsof -ti:8081 | xargs kill
```

### Docker issues
```bash
# Restart Docker
docker-compose down
docker-compose up -d db redis acapy
```

### Mobile app won't load
```bash
# Clear Expo cache
cd apps/mobile
npx expo start --clear
```

### Slow performance
The demo is optimized for MacBook Air M1 8GB. If using older hardware:
- Close other applications
- Disable ACA-Py if not demonstrating SSI features: `docker-compose stop acapy`
- Use Chrome for best performance

## Next Steps

1. **Run the demo:** `./scripts/start-demo.sh`
2. **Follow the 5-minute flow above**
3. **Record your own demo video** (optional)
4. **Share with stakeholders**
