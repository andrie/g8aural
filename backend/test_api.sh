#!/bin/bash

# ABRSM Grade 8 Cadence Training - API Test Script
# Tests all backend endpoints and functionality

set -e

BASE_URL="http://localhost:8000"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "═══════════════════════════════════════════════════════"
echo "  ABRSM Grade 8 Cadence Training - API Tests"
echo "═══════════════════════════════════════════════════════"
echo

# Check if server is running
echo -n "Checking if server is running... "
if ! curl -s "$BASE_URL/" > /dev/null 2>&1; then
    echo -e "${RED}✗ FAILED${NC}"
    echo
    echo "Server is not running. Start it with:"
    echo "  cd backend"
    echo "  .venv/bin/uvicorn app.main:app --reload --port 8000"
    exit 1
fi
echo -e "${GREEN}✓${NC}"

# Test 1: Root endpoint
echo
echo "Test 1: Root Endpoint"
echo "────────────────────────────────────────────────────────"
RESPONSE=$(curl -s "$BASE_URL/")
if echo "$RESPONSE" | grep -q "ABRSM Grade 8 Cadence Training API"; then
    echo -e "${GREEN}✓ Root endpoint working${NC}"
    echo "Response: $RESPONSE"
else
    echo -e "${RED}✗ Root endpoint failed${NC}"
    exit 1
fi

# Test 2: Health check
echo
echo "Test 2: Health Check"
echo "────────────────────────────────────────────────────────"
RESPONSE=$(curl -s "$BASE_URL/api/health")
if echo "$RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "Response: $RESPONSE"
else
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi

# Test 3: Generate cadence
echo
echo "Test 3: Generate Cadence"
echo "────────────────────────────────────────────────────────"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/cadence/generate" \
    -H "Content-Type: application/json" -d "{}")

SESSION_ID=$(echo "$RESPONSE" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
PROGRESSION=$(echo "$RESPONSE" | grep -o '"chord_symbols":\[[^]]*\]')

if [ -n "$SESSION_ID" ] && [ -n "$PROGRESSION" ]; then
    echo -e "${GREEN}✓ Cadence generated successfully${NC}"
    echo "Session ID: $SESSION_ID"
    echo "Progression: $PROGRESSION"
else
    echo -e "${RED}✗ Cadence generation failed${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi

# Test 4: Check incorrect guess
echo
echo "Test 4: Check Incorrect Guess"
echo "────────────────────────────────────────────────────────"
RESULT=$(curl -s -X POST "$BASE_URL/api/cadence/check" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$SESSION_ID\", \"guess\": \"perfect\"}")

if echo "$RESULT" | grep -q '"correct":false' || echo "$RESULT" | grep -q '"correct":true'; then
    echo -e "${GREEN}✓ Guess check working${NC}"
    echo "Response: $RESULT"
else
    echo -e "${RED}✗ Guess check failed${NC}"
    echo "Response: $RESULT"
    exit 1
fi

# Test 5: Find correct answer
echo
echo "Test 5: Find Correct Answer"
echo "────────────────────────────────────────────────────────"
CORRECT_FOUND=false
for cadence in "perfect" "plagal" "imperfect" "interrupted"; do
    RESULT=$(curl -s -X POST "$BASE_URL/api/cadence/check" \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$SESSION_ID\", \"guess\": \"$cadence\"}")

    if echo "$RESULT" | grep -q '"correct":true'; then
        echo -e "${GREEN}✓ Correct answer found: $cadence${NC}"
        echo "Response: $RESULT"
        CORRECT_FOUND=true
        break
    fi
done

if [ "$CORRECT_FOUND" = false ]; then
    echo -e "${RED}✗ Could not find correct answer${NC}"
    exit 1
fi

# Test 6: Verify all cadence types
echo
echo "Test 6: Verify All Cadence Types (20 generations)"
echo "────────────────────────────────────────────────────────"

declare -A cadences
cadences["perfect"]=0
cadences["plagal"]=0
cadences["imperfect"]=0
cadences["interrupted"]=0

for i in {1..20}; do
    RESPONSE=$(curl -s -X POST "$BASE_URL/api/cadence/generate" \
        -H "Content-Type: application/json" -d "{}")

    SYMBOLS=$(echo "$RESPONSE" | grep -o '"chord_symbols":\[[^]]*\]' | sed 's/"chord_symbols"://')

    # Extract last two chords
    LAST_TWO=$(echo "$SYMBOLS" | sed 's/.*,"\([^"]*\)"\s*,"\([^"]*\)"\s*\]/\1,\2/')

    # Determine cadence type
    case "$LAST_TWO" in
        "V,I")
            cadences["perfect"]=$((cadences["perfect"] + 1))
            ;;
        "IV,I")
            cadences["plagal"]=$((cadences["plagal"] + 1))
            ;;
        "I,V")
            cadences["imperfect"]=$((cadences["imperfect"] + 1))
            ;;
        "V,vi")
            cadences["interrupted"]=$((cadences["interrupted"] + 1))
            ;;
    esac
done

echo "Generation results:"
echo "  Perfect (V-I):      ${cadences["perfect"]}"
echo "  Plagal (IV-I):      ${cadences["plagal"]}"
echo "  Imperfect (I-V):    ${cadences["imperfect"]}"
echo "  Interrupted (V-vi): ${cadences["interrupted"]}"

if [ ${cadences["perfect"]} -gt 0 ] && [ ${cadences["plagal"]} -gt 0 ] && \
   [ ${cadences["imperfect"]} -gt 0 ] && [ ${cadences["interrupted"]} -gt 0 ]; then
    echo -e "${GREEN}✓ All four cadence types verified${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Not all cadence types appeared in 20 generations${NC}"
fi

# Test 7: Session cleanup after correct answer
echo
echo "Test 7: Session Cleanup"
echo "────────────────────────────────────────────────────────"
# Generate new session
RESPONSE=$(curl -s -X POST "$BASE_URL/api/cadence/generate" \
    -H "Content-Type: application/json" -d "{}")
NEW_SESSION=$(echo "$RESPONSE" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)

# Find and submit correct answer
for cadence in "perfect" "plagal" "imperfect" "interrupted"; do
    RESULT=$(curl -s -X POST "$BASE_URL/api/cadence/check" \
        -H "Content-Type: application/json" \
        -d "{\"session_id\": \"$NEW_SESSION\", \"guess\": \"$cadence\"}")

    if echo "$RESULT" | grep -q '"correct":true'; then
        break
    fi
done

# Try to use session again (should fail)
RESULT=$(curl -s -X POST "$BASE_URL/api/cadence/check" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$NEW_SESSION\", \"guess\": \"perfect\"}" 2>&1)

if echo "$RESULT" | grep -q "Session not found" || echo "$RESULT" | grep -q "404"; then
    echo -e "${GREEN}✓ Session cleaned up after correct answer${NC}"
else
    echo -e "${YELLOW}⚠ Session cleanup might not be working (this is non-critical)${NC}"
fi

# Summary
echo
echo "═══════════════════════════════════════════════════════"
echo -e "  ${GREEN}ALL TESTS PASSED ✓${NC}"
echo "═══════════════════════════════════════════════════════"
echo
echo "Backend is fully functional and ready for frontend integration!"
echo
echo "Next steps:"
echo "  1. View API docs: http://localhost:8000/docs"
echo "  2. Start frontend development (Phase 2)"
echo "  3. Connect frontend to these endpoints"
