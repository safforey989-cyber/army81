#!/bin/bash
# ══════════════════════════════════════════════════════════════
# Army81 - Deploy to Google Cloud Run
# نشر على Google Cloud Run
# المرحلة 3: البنية التحتية
# ══════════════════════════════════════════════════════════════

set -e

# ── Configuration ──────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="army81-gateway"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
MEMORY="2Gi"
CPU="2"
MIN_INSTANCES="0"
MAX_INSTANCES="5"
PORT="8181"
TIMEOUT="300"

# ── Colors ──────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   Army81 — Google Cloud Run Deployment${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"

# ── Validation ──────────────────────────────────────────────────
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP_PROJECT_ID not set${NC}"
    echo "Set it with: export GCP_PROJECT_ID=your-project-id"
    exit 1
fi

# Check gcloud
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found${NC}"
    echo "Install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo -e "${YELLOW}Project: ${PROJECT_ID}${NC}"
echo -e "${YELLOW}Region:  ${REGION}${NC}"
echo -e "${YELLOW}Service: ${SERVICE_NAME}${NC}"
echo ""

# ── Step 1: Enable APIs ────────────────────────────────────────
echo -e "${GREEN}[1/5] Enabling required APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    firestore.googleapis.com \
    cloudscheduler.googleapis.com \
    pubsub.googleapis.com \
    --project="${PROJECT_ID}" \
    --quiet

# ── Step 2: Build Docker Image ─────────────────────────────────
echo -e "${GREEN}[2/5] Building Docker image...${NC}"
cd "$(dirname "$0")/.."

gcloud builds submit \
    --tag "${IMAGE_NAME}" \
    --project="${PROJECT_ID}" \
    --timeout="600s" \
    --quiet

echo -e "${GREEN}Image built: ${IMAGE_NAME}${NC}"

# ── Step 3: Deploy to Cloud Run ────────────────────────────────
echo -e "${GREEN}[3/5] Deploying to Cloud Run...${NC}"

# Collect env vars from .env file if exists
ENV_VARS=""
if [ -f .env ]; then
    while IFS= read -r line; do
        # Skip comments and empty lines
        [[ "$line" =~ ^#.*$ ]] && continue
        [[ -z "$line" ]] && continue
        # Skip if no = sign
        [[ "$line" != *"="* ]] && continue

        key=$(echo "$line" | cut -d= -f1)
        value=$(echo "$line" | cut -d= -f2-)

        # Skip empty values
        [[ -z "$value" ]] && continue

        if [ -z "$ENV_VARS" ]; then
            ENV_VARS="${key}=${value}"
        else
            ENV_VARS="${ENV_VARS},${key}=${value}"
        fi
    done < .env
fi

# Always add GCP_PROJECT_ID
if [ -z "$ENV_VARS" ]; then
    ENV_VARS="GCP_PROJECT_ID=${PROJECT_ID}"
else
    ENV_VARS="${ENV_VARS},GCP_PROJECT_ID=${PROJECT_ID}"
fi

gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_NAME}" \
    --region "${REGION}" \
    --project "${PROJECT_ID}" \
    --memory "${MEMORY}" \
    --cpu "${CPU}" \
    --min-instances "${MIN_INSTANCES}" \
    --max-instances "${MAX_INSTANCES}" \
    --port "${PORT}" \
    --timeout "${TIMEOUT}" \
    --set-env-vars="${ENV_VARS}" \
    --allow-unauthenticated \
    --quiet

# ── Step 4: Get URL ────────────────────────────────────────────
echo -e "${GREEN}[4/5] Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --format="value(status.url)")

echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"

# ── Step 5: Health Check ──────────────────────────────────────
echo -e "${GREEN}[5/5] Running health check...${NC}"
sleep 5

HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/health" 2>/dev/null || echo "failed")

if [ "$HEALTH" = "200" ]; then
    echo -e "${GREEN}Health check passed!${NC}"
else
    echo -e "${YELLOW}Health check returned: ${HEALTH} (service may still be starting)${NC}"
fi

# ── Summary ──────────────────────────────────────────────────
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   Deployment Complete!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  URL:     ${SERVICE_URL}"
echo -e "  Status:  ${SERVICE_URL}/status"
echo -e "  Health:  ${SERVICE_URL}/health"
echo -e "  Agents:  ${SERVICE_URL}/agents"
echo ""
echo -e "  Test:"
echo -e "    curl ${SERVICE_URL}/health"
echo -e "    curl -X POST ${SERVICE_URL}/task -H 'Content-Type: application/json' \\"
echo -e "      -d '{\"task\": \"ما أهم أخبار الذكاء الاصطناعي اليوم؟\"}'"
echo ""
