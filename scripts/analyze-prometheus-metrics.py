#!/usr/bin/env python3
"""
Analyze probe execution times from Prometheus metrics
Generate recommendations for GKE 1.35 timeoutSeconds configuration
"""

import requests
import json
import sys
import argparse
from datetime import datetime, timedelta
import subprocess
from typing import Dict, List

class PrometheusAnalyzer:
    def __init__(self, prometheus_url: str, use_cloud_monitoring: bool = False):
        self.prometheus_url = prometheus_url.rstrip('/')
        self.use_cloud_monitoring = use_cloud_monitoring
        self.recommendations = []
        
    def query_prometheus(self, query: str) -> dict:
        """Execute a PromQL query"""
        endpoint = f"{self.prometheus_url}/api/v1/query"
        params = {'query': query}
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error querying Prometheus: {e}")
            return None
    
    def get_p99_durations(self) -> Dict[str, float]:
        """Get P99 probe durations for all workloads"""
        query = """
        histogram_quantile(0.99,
            sum(rate(kubernetes_probe_duration_seconds_bucket[24h])) 
            by (namespace, pod, container, probe_type, le)
        )
        """
        
        result = self.query_prometheus(query)
        if not result or result.get('status') != 'success':
            return {}
        
        durations = {}
        for item in result.get('data', {}).get('result', []):
            metric = item['metric']
            value = float(item['value'][1])
            
            key = f"{metric['namespace']}/{metric['pod']}/{metric['container']}/{metric['probe_type']}"
            durations[key] = value
        
        return durations
    
    def get_violation_percentage(self) -> Dict[str, float]:
        """Get percentage of probes exceeding 1s"""
        query = """
        100 * (
            sum(rate(kubernetes_probe_timeout_violations_total[24h])) by (namespace, pod, container, probe_type)
            /
            sum(rate(kubernetes_probe_observations_total[24h])) by (namespace, pod, container, probe_type)
        )
        """
        
        result = self.query_prometheus(query)
        if not result or result.get('status') != 'success':
            return {}
        
        percentages = {}
        for item in result.get('data', {}).get('result', []):
            metric = item['metric']
            value = float(item['value'][1])
            
            key = f"{metric['namespace']}/{metric['pod']}/{metric['container']}/{metric['probe_type']}"
            percentages[key] = value
        
        return percentages
    
    def calculate_recommendations(self) -> List[Dict]:
        """Calculate timeout recommendations based on metrics"""
        p99_durations = self.get_p99_durations()
        violation_percentages = self.get_violation_percentage()
        
        recommendations = []
        
        for key, p99 in p99_durations.items():
            namespace, pod, container, probe_type = key.split('/')
            
            # Calculate recommended timeout (P99 + 20% buffer)
            recommended_timeout = max(1, int(p99 * 1.2) + 1)
            
            violation_pct = violation_percentages.get(key, 0)
            
            if violation_pct > 0:
                recommendations.append({
                    'namespace': namespace,
                    'pod': pod,
                    'container': container,
                    'probe_type': probe_type,
                    'p99_duration': round(p99, 2),
                    'violation_percentage': round(violation_pct, 1),
                    'current_impact': 'HIGH' if violation_pct > 50 else 'MEDIUM' if violation_pct > 10 else 'LOW',
                    'recommended_timeout': recommended_timeout,
                    'patch_required': p99 > 1.0
                })
        
        recommendations.sort(key=lambda x: x['violation_percentage'], reverse=True)
        return recommendations
    
    def generate_report(self, recommendations: List[Dict]):
        """Generate comprehensive report"""
        print("\n" + "="*80)
        print("PROMETHEUS-BASED PROBE ANALYSIS REPORT")
        print("GKE 1.35 ExecProbeTimeout Preparation")
        print("="*80 + "\n")
        
        if not recommendations:
            print("✅ No probes exceeding 1s timeout threshold found!")
            print("Your cluster appears ready for GKE 1.35")
            return
        
        total_probes = len(recommendations)
        high_impact = len([r for r in recommendations if r['current_impact'] == 'HIGH'])
        medium_impact = len([r for r in recommendations if r['current_impact'] == 'MEDIUM'])
        low_impact = len([r for r in recommendations if r['current_impact'] == 'LOW'])
        
        print(f"📊 SUMMARY")
        print(f"  Total probes needing attention: {total_probes}")
        print(f"  High impact (>50% violations): {high_impact}")
        print(f"  Medium impact (10-50% violations): {medium_impact}")
        print(f"  Low impact (<10% violations): {low_impact}")
        print()
        
        print("🚨 TOP 10 CRITICAL WORKLOADS")
        print("-" * 80)
        
        for i, rec in enumerate(recommendations[:10], 1):
            print(f"\n{i}. {rec['namespace']}/{rec['pod']}")
            print(f"   Container: {rec['container']}")
            print(f"   Probe Type: {rec['probe_type']}")
            print(f"   P99 Duration: {rec['p99_duration']}s")
            print(f"   Violation Rate: {rec['violation_percentage']}%")
            print(f"   Recommended timeoutSeconds: {rec['recommended_timeout']}")
        
        # Save detailed report
        report_file = f"prometheus-probe-analysis-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total': total_probes,
                    'high_impact': high_impact,
                    'medium_impact': medium_impact,
                    'low_impact': low_impact
                },
                'recommendations': recommendations
            }, f, indent=2)
        
        print(f"\n📁 Detailed report saved to: {report_file}")
    
    def run_analysis(self):
        """Run the complete analysis"""
        print("🔍 Querying Prometheus for probe metrics...")
        
        recommendations = self.calculate_recommendations()
        self.generate_report(recommendations)
        
        return recommendations

def main():
    parser = argparse.ArgumentParser(
        description='Analyze probe metrics from Prometheus for GKE 1.35 preparation'
    )
    parser.add_argument(
        '--prometheus-url',
        default='http://localhost:9090',
        help='Prometheus server URL (default: http://localhost:9090)'
    )
    parser.add_argument(
        '--cloud-monitoring',
        action='store_true',
        help='Use Google Cloud Monitoring instead of Prometheus'
    )
    
    args = parser.parse_args()
    
    analyzer = PrometheusAnalyzer(
        prometheus_url=args.prometheus_url,
        use_cloud_monitoring=args.cloud_monitoring
    )
    
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
