#!/bin/bash
# Audit script for exec probes in preparation for GKE 1.35

set -e

REPORT_FILE="gke-1.35-probe-audit-$(date +%Y%m%d-%H%M%S).md"
JSON_REPORT="gke-1.35-probe-audit-$(date +%Y%m%d-%H%M%S).json"
NAMESPACE_FILTER="${1:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}GKE 1.35 Exec Probe Timeout Audit${NC}"
echo -e "${BLUE}=====================================${NC}\n"

# Initialize report
cat > "$REPORT_FILE" << EEOF
# GKE 1.35 Exec Probe Timeout Audit Report
Generated: $(date)

## Executive Summary
This report identifies all workloads with exec probes that may be affected by the 
ExecProbeTimeout enforcement in GKE 1.35.

EEOF

# Function to check a specific resource type
audit_resource_type() {
    local resource_type=$1
    local namespace_option=$2
    
    echo -e "${YELLOW}Auditing $resource_type...${NC}"
    echo "## $resource_type" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    local found_issues=0
    
    kubectl get "$resource_type" $namespace_option -o json 2>/dev/null | \
    jq -r '.items[] | 
        select(.spec.template.spec.containers[]? | 
            (.livenessProbe?.exec? // false) or 
            (.readinessProbe?.exec? // false) or 
            (.startupProbe?.exec? // false)) |
        "\(.metadata.namespace)|\(.metadata.name)"' | \
    while IFS='|' read -r namespace name; do
        echo -n "  Checking $namespace/$name... "
        
        local probe_info=$(kubectl get "$resource_type" "$name" -n "$namespace" -o json | \
            jq -r '.spec.template.spec.containers[] | 
                select((.livenessProbe?.exec? // false) or 
                       (.readinessProbe?.exec? // false) or 
                       (.startupProbe?.exec? // false)) |
                {
                    container: .name,
                    liveness: .livenessProbe,
                    readiness: .readinessProbe,
                    startup: .startupProbe
                }')
        
        echo "$probe_info" | jq -c '.' | while read -r container_config; do
            local container_name=$(echo "$container_config" | jq -r '.container')
            local has_issue=false
            local issue_details=""
            
            local liveness_timeout=$(echo "$container_config" | jq -r '.liveness.timeoutSeconds // "not_set"')
            if [ "$(echo "$container_config" | jq -r '.liveness.exec // false')" != "false" ] && [ "$liveness_timeout" = "not_set" ]; then
                has_issue=true
                issue_details="${issue_details}  - ⚠️  Liveness probe missing timeoutSeconds (will default to 1s)\n"
            fi
            
            local readiness_timeout=$(echo "$container_config" | jq -r '.readiness.timeoutSeconds // "not_set"')
            if [ "$(echo "$container_config" | jq -r '.readiness.exec // false')" != "false" ] && [ "$readiness_timeout" = "not_set" ]; then
                has_issue=true
                issue_details="${issue_details}  - ⚠️  Readiness probe missing timeoutSeconds (will default to 1s)\n"
            fi
            
            local startup_timeout=$(echo "$container_config" | jq -r '.startup.timeoutSeconds // "not_set"')
            if [ "$(echo "$container_config" | jq -r '.startup.exec // false')" != "false" ] && [ "$startup_timeout" = "not_set" ]; then
                has_issue=true
                issue_details="${issue_details}  - ⚠️  Startup probe missing timeoutSeconds (will default to 1s)\n"
            fi
            
            if [ "$has_issue" = true ]; then
                echo -e "${RED}NEEDS ATTENTION${NC}"
                found_issues=$((found_issues + 1))
                
                cat >> "$REPORT_FILE" << EEOF

### ⚠️ $namespace/$name
**Container:** $container_name
**Issues:**
$(echo -e "$issue_details")
**Action Required:** Add explicit timeoutSeconds to exec probes

EEOF
            else
                echo -e "${GREEN}OK${NC}"
            fi
        done
    done
    
    if [ $found_issues -eq 0 ]; then
        echo "✅ No issues found in $resource_type" >> "$REPORT_FILE"
    fi
    
    echo "" >> "$REPORT_FILE"
}

# Build namespace filter
if [ -n "$NAMESPACE_FILTER" ]; then
    NAMESPACE_OPTION="-n $NAMESPACE_FILTER"
    echo "Filtering by namespace: $NAMESPACE_FILTER"
else
    NAMESPACE_OPTION="--all-namespaces"
    echo "Scanning all namespaces"
fi

# Audit different resource types
audit_resource_type "deployments" "$NAMESPACE_OPTION"
audit_resource_type "statefulsets" "$NAMESPACE_OPTION"
audit_resource_type "daemonsets" "$NAMESPACE_OPTION"

# Generate JSON report
echo -e "\n${YELLOW}Generating JSON report...${NC}"

kubectl get deployments,statefulsets,daemonsets $NAMESPACE_OPTION -o json 2>/dev/null | \
jq '[.items[] | 
    select(.spec.template.spec.containers[]? | 
        (.livenessProbe?.exec? // false) or 
        (.readinessProbe?.exec? // false) or 
        (.startupProbe?.exec? // false)) |
    {
        kind: .kind,
        namespace: .metadata.namespace,
        name: .metadata.name
    }] | 
    {
        audit_date: now | todate,
        total_resources: length
    }' > "$JSON_REPORT"

echo -e "\n${BLUE}=====================================${NC}"
echo -e "${BLUE}Audit Complete${NC}"
echo -e "${BLUE}=====================================${NC}\n"

echo "Reports generated:"
echo "  - Detailed report: $REPORT_FILE"
echo "  - JSON report: $JSON_REPORT"

echo -e "\n${GREEN}Audit complete!${NC}"
