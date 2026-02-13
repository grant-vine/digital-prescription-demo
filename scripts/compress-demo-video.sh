#!/bin/bash
#
# compress-demo-video.sh
# Compress WebM demo videos into a single side-by-side MP4 for investor presentations
#
# Usage: ./scripts/compress-demo-video.sh
# Output: demo-investor-final.mp4 (project root)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VIDEO_DIR="$PROJECT_ROOT/apps/mobile/test-results/videos"
OUTPUT_FILE="$PROJECT_ROOT/demo-investor-final.mp4"
TEMP_DIR=$(mktemp -d)

cleanup() {
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  FFmpeg Demo Video Compression (3-Panel Layout)   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"

# Check if video directory exists
if [ ! -d "$VIDEO_DIR" ]; then
  echo -e "${RED}✗ Error: Video directory not found: $VIDEO_DIR${NC}"
  exit 1
fi

# Find all WebM videos (bash 3.x compatible)
VIDEOS=()
while IFS= read -r video; do
  VIDEOS+=("$video")
done < <(find "$VIDEO_DIR" -maxdepth 1 -name "*.webm" -type f | sort)

if [ ${#VIDEOS[@]} -ne 3 ]; then
  echo -e "${RED}✗ Error: Expected 3 WebM videos, found ${#VIDEOS[@]}${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Found 3 WebM videos${NC}"

# Get video info
total_duration=0
for i in "${!VIDEOS[@]}"; do
  video="${VIDEOS[$i]}"
  filename=$(basename "$video")
  filesize=$(du -h "$video" | cut -f1)
  
  # Get duration
  duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1:noprint_wrappers=1 "$video" 2>/dev/null || echo "0")
  duration=${duration%.*}  # Remove decimal
  total_duration=$((total_duration + duration))
  
  role_name=("Doctor" "Patient" "Pharmacist")
  echo -e "${YELLOW}  [${i}] ${role_name[$i]}: $filename ($filesize, ${duration}s)${NC}"
done

echo -e "${YELLOW}  Total duration: ${total_duration}s (~$(( (total_duration + 30) / 60 ))min)${NC}"

echo ""
echo -e "${BLUE}Compressing to MP4 with 3-panel side-by-side layout...${NC}"
echo -e "  Output: $OUTPUT_FILE"
echo -e "  Codec: H.264 (libx264)"
echo -e "  CRF: 28 (quality/size balance)"
echo -e "  Resolution: 1280x720 (3 panels × 426x720)"
echo -e "  Pixel format: yuv420p (universal compatibility)"
echo -e "  Preset: fast"
echo ""

# Build ffmpeg command with dynamic video inputs
# Layout: each video is 1280x720, scale to 426x720 (1280/3), then hstack side-by-side
# Each panel: 426x720
# Total: 1280x720 (426*3 = 1278, close enough)

ffmpeg \
  -i "${VIDEOS[0]}" \
  -i "${VIDEOS[1]}" \
  -i "${VIDEOS[2]}" \
  -filter_complex "[0:v]scale=426:720[v0]; [1:v]scale=426:720[v1]; [2:v]scale=426:720[v2]; [v0][v1][v2]hstack=inputs=3[v]" \
  -map "[v]" \
  -c:v libx264 \
  -crf 28 \
  -preset fast \
  -r 30 \
  -pix_fmt yuv420p \
  -movflags +faststart \
  -shortest \
  "$OUTPUT_FILE" \
  2>&1

# Check if output file exists
if [ ! -f "$OUTPUT_FILE" ]; then
  echo -e "${RED}✗ Error: Failed to create output file${NC}"
  exit 1
fi

echo ""
echo -e "${GREEN}✓ Compression complete!${NC}"

# Get file stats
filesize_mb=$(du -h "$OUTPUT_FILE" | cut -f1)
filesize_bytes=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
filesize_mb_val=$(echo "scale=2; $filesize_bytes / 1048576" | bc)

echo -e "${YELLOW}  Output file: $OUTPUT_FILE${NC}"
echo -e "${YELLOW}  File size: ${filesize_mb} (${filesize_mb_val} MB)${NC}"

# Check file size
if (( $(echo "$filesize_mb_val > 10" | bc -l) )); then
  echo -e "${YELLOW}⚠ Warning: File size > 10MB. Attempting re-compression with CRF=30...${NC}"
  
  ffmpeg \
    -i "${VIDEOS[0]}" \
    -i "${VIDEOS[1]}" \
    -i "${VIDEOS[2]}" \
    -filter_complex "[0:v]scale=426:720[v0]; [1:v]scale=426:720[v1]; [2:v]scale=426:720[v2]; [v0][v1][v2]hstack=inputs=3[v]" \
    -map "[v]" \
    -c:v libx264 \
    -crf 30 \
    -preset fast \
    -r 30 \
    -pix_fmt yuv420p \
    -movflags +faststart \
    -shortest \
    "${OUTPUT_FILE}.tmp" \
    2>&1
  
  mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
  
  filesize_mb=$(du -h "$OUTPUT_FILE" | cut -f1)
  filesize_bytes=$(stat -c%s "$OUTPUT_FILE" 2>/dev/null || stat -f%z "$OUTPUT_FILE" 2>/dev/null)
  filesize_mb_val=$(echo "scale=2; $filesize_bytes / 1048576" | bc)
  echo -e "${YELLOW}  Re-compressed size: ${filesize_mb} (${filesize_mb_val} MB)${NC}"
fi

# Verify with ffprobe
echo ""
echo -e "${BLUE}Verifying MP4 with ffprobe...${NC}"
ffprobe_output=$(ffprobe -v error -show_format -show_streams "$OUTPUT_FILE" 2>&1)

codec=$(echo "$ffprobe_output" | grep "codec_name=h264" || echo "")
if [ -z "$codec" ]; then
  echo -e "${YELLOW}⚠ Warning: H.264 codec not found in ffprobe output${NC}"
else
  echo -e "${GREEN}✓ Codec verified: H.264${NC}"
fi

resolution=$(echo "$ffprobe_output" | grep -E "^width|^height" | head -2)
echo -e "${GREEN}✓ Resolution: $(echo "$resolution" | tr '\n' ' ')${NC}"

duration=$(echo "$ffprobe_output" | grep "duration=" | head -1 | cut -d'=' -f2)
echo -e "${GREEN}✓ Duration: ${duration}s${NC}"

# Final verification
echo ""
if [ -f "$OUTPUT_FILE" ]; then
  echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
  echo -e "${GREEN}║  ✓ Video compression successful!                   ║${NC}"
  echo -e "${GREEN}║  File: demo-investor-final.mp4                     ║${NC}"
  echo -e "${GREEN}║  Size: ${filesize_mb} (${filesize_mb_val} MB)${NC}"
  echo -e "${GREEN}║  Format: MP4 (H.264, 1278x720, 30fps)             ║${NC}"
  echo -e "${GREEN}║  Layout: 3-panel side-by-side (Doctor|Patient|Rx) ║${NC}"
  echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
  exit 0
else
  echo -e "${RED}✗ Error: Output verification failed${NC}"
  exit 1
fi
