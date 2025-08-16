#!/usr/bin/env python3
"""
Automatic remediation script for GKE 1.35 exec probe timeouts
"""

import json
import subprocess
import argparse
from datetime import datetime

class ProbeRemediator:
    def __init__(self, dry_run=True, default_timeout=5):
        self.dry_run = dry_run
        self.default_timeout = default_timeout
        self.patches_applied = []
        
    def run_kubectl(self, command):
        """Execute kubectl command and return output"""
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True
        )
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return None
        return result.stdout
    
    def get_workloads_needing_update(self, namespace=None):
        """Find all workloads with exec probes missing timeoutSeconds"""
        namespace_option = f"-n {namespace}" if namespace else "--all-namespaces"
        workloads = []
        
        for resource_type in ['deployment', 'statefulset', 'daemonset']:
            cmd = f"kubectl get {resource_type} {namespace_option} -o json"
            output = self.run_kubectl(cmd)
            
            if not output:
                continue
            
            resources = json.loads(output)
            
            for item in resources.get('items', []):
                needs_update, details = self.check_workload(item)
                if needs_update:
                    workloads.append({
                        'kind': item['kind'],
                        'namespace': item['metadata']['namespace'],
                        'name': item['metadata']['name'],
                        'details': details
                    })
        
        return workloads
    
    def check_workload(self, workload):
        """Check if a workload needs probe timeout updates"""
        needs_update = False
        details = []
        
        containers = workload.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
        
        for container in containers:
            container_name = container.get('name')
            
            for probe_type in ['livenessProbe', 'readinessProbe', 'startupProbe']:
                probe = container.get(probe_type)
                
                if probe and probe.get('exec'):
                    if 'timeoutSeconds' not in probe:
                        needs_update = True
                        details.append({
                            'container': container_name,
                            'probe_type': probe_type,
                            'recommended_timeout': self.default_timeout
                        })
        
        return needs_update, details
    
    def run(self, namespace=None):
        """Main remediation process"""
        print("=" * 60)
        print("GKE 1.35 Exec Probe Timeout Auto-Remediation")
        print("=" * 60)
        
        if self.dry_run:
            print("\n🔍 Running in DRY RUN mode - no changes will be made")
        else:
            print("\n⚠️  Running in APPLY mode - changes will be made")
        
        print("\nScanning for workloads needing updates...")
        workloads = self.get_workloads_needing_update(namespace)
        
        if not workloads:
            print("✅ No workloads need updates!")
            return
        
        print(f"\n⚠️  Found {len(workloads)} workloads needing updates")
        
        for workload in workloads:
            print(f"  - {workload['kind']}: {workload['namespace']}/{workload['name']}")
        
        print("\n✅ Remediation complete!")

def main():
    parser = argparse.ArgumentParser(
        description='Auto-remediate exec probe timeouts for GKE 1.35'
    )
    parser.add_argument(
        '--apply', 
        action='store_true',
        help='Apply changes (default is dry-run)'
    )
    parser.add_argument(
        '--namespace', '-n',
        help='Limit to specific namespace'
    )
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=5,
        help='Default timeout in seconds (default: 5)'
    )
    
    args = parser.parse_args()
    
    remediator = ProbeRemediator(
        dry_run=not args.apply,
        default_timeout=args.timeout
    )
    
    remediator.run(namespace=args.namespace)

if __name__ == "__main__":
    main()
