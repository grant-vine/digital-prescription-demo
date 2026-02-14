#!/bin/bash
#
# generate-demo-videos.sh
# Generate 3 separate demo videos for each role
#
# Usage: ./scripts/generate-demo-videos.sh
# Output: 
#   - demo-doctor.mp4
#   - demo-patient.mp4  
#   - demo-pharmacist.mp4

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VIDEO_DIR="$PROJECT_ROOT/apps/mobile/test-results/videos"

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Generate Demo Videos (3 Separate Files)          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Run the Playwright tests to generate videos
echo -e "${YELLOW}Running Playwright tests to generate videos...${NC}"
cd "$PROJECT_ROOT/apps/mobile"

# Run each test separately to get individual videos
echo -e "${BLUE}Recording Doctor workflow...${NC}"
npx playwright test e2e/demo-video.spec.ts --grep "Doctor:" --reporter=line 2>&1 | grep -E "(passed|failed|Error)" || true

echo -e "${BLUE}Recording Patient workflow...${NC}"
npx playwright test e2e/demo-video.spec.ts --grep "Patient:" --reporter=line 2>&1 | grep -E "(passed|failed|Error)" || true

echo -e "${BLUE}Recording Pharmacist workflow...${NC}"
npx playwright test e2e/demo-video.spec.ts --grep "Pharmacist:" --reporter=line 2>&1 | grep -E "(passed|failed|Error)" || true

echo ""
echo -e "${GREEN}✓ Video generation complete${NC}"
echo ""

# Check for generated videos
for role in doctor patient pharmacist; do
  ROLE_DIR="$VIDEO_DIR/$role"
  if [ -d "$ROLE_DIR" ]; then
    VIDEO_COUNT=$(find "$ROLE_DIR" -name "*.webm" -type f | wc -l)
    if [ "$VIDEO_COUNT" -gt 0 ]; then
      echo -e "${GREEN}✓ $role: $VIDEO_COUNT video(s) generated${NC}"
      
      # Get the most recent video
      LATEST_VIDEO=$(find "$ROLE_DIR" -name "*.webm" -type f -exec ls -t {} + | head -1)
      if [ -n "$LATEST_VIDEO" ]; then
        BASENAME=$(basename "$LATEST_VIDEO" .webm)
        OUTPUT_FILE="$PROJECT_ROOT/demo-$role.mp4"
        
        echo -e "${BLUE}Converting $role video to MP4...${NC}"
        ffmpeg -i "$LATEST_VIDEO" \
          -c:v libx264 \
          -crf 28 \
          -preset fast \
          -r 30 \
          -pix_fmt yuv420p \
          -movflags +faststart \
          "$OUTPUT_FILE" \
          -y \
          2>&1 | grep -E "(frame|Output|error)" || true
        
        if [ -f "$OUTPUT_FILE" ]; then
          FILESIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
          echo -e "${GREEN}✓ demo-$role.mp4 created ($FILESIZE)${NC}"
        fi
      fi
    else
      echo -e "${RED}✗ $role: No videos found${NC}"
    fi
  else
    echo -e "${RED}✗ $role: Directory not found${NC}"
  fi
done

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Demo Videos Generated!                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Files created:"
for role in doctor patient pharmacist; do
  FILE="$PROJECT_ROOT/demo-$role.mp4"
  if [ -f "$FILE" ]; then
    FILESIZE=$(du -h "$FILE" | cut -f1)
    DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$FILE" 2>/dev/null | cut -d. -f1)
    echo -e "  ${GREEN}✓ demo-$role.mp4${NC} ($FILESIZE, ${DURATION}s)"
  fi
done
echo ""
