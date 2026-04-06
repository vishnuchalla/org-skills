#!/usr/bin/env python3
"""
Elasticsearch Asset Validator for Orion Claude Skill

This script validates the elasticsearch-config.yaml asset configuration
and tests connectivity to ensure proper setup.

Usage:
    python3 validate-es-asset.py [asset-path]
    
Examples:
    python3 validate-es-asset.py
    python3 validate-es-asset.py assets/elasticsearch-config.yaml
    python3 validate-es-asset.py ~/.claude/skills/orion/elasticsearch-config.yaml
"""

import sys
import os
import yaml
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import argparse


class Colors:
    """Terminal colors for output formatting."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


class ESAssetValidator:
    """Validates Elasticsearch asset configuration and connectivity."""
    
    def __init__(self, asset_path: Optional[str] = None):
        """Initialize validator with asset path."""
        self.asset_path = self._find_asset_path(asset_path)
        self.config = None
        self.errors = []
        self.warnings = []
        
    def _find_asset_path(self, provided_path: Optional[str]) -> str:
        """Find the elasticsearch-config.yaml asset file."""
        search_paths = []
        
        if provided_path:
            search_paths.append(provided_path)
        
        # Add common asset locations
        search_paths.extend([
            "assets/elasticsearch-config.yaml",
            "elasticsearch-config.yaml",
            os.path.expanduser("~/.claude/skills/orion-regression-analysis/assets/elasticsearch-config.yaml"),
            os.path.expanduser("~/.orion/elasticsearch-config.yaml"),
        ])
        
        # Check ORION_SKILL_DIR environment variable
        if 'ORION_SKILL_DIR' in os.environ:
            search_paths.append(
                os.path.join(os.environ['ORION_SKILL_DIR'], 'assets', 'elasticsearch-config.yaml')
            )
        
        for path in search_paths:
            if os.path.isfile(path):
                return path
                
        # If not found, return the first search path for error reporting
        return search_paths[0] if search_paths else "elasticsearch-config.yaml"
    
    def _log_info(self, message: str):
        """Log info message with color."""
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")
    
    def _log_success(self, message: str):
        """Log success message with color."""
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")
    
    def _log_warning(self, message: str):
        """Log warning message with color."""
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")
        self.warnings.append(message)
    
    def _log_error(self, message: str):
        """Log error message with color."""
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")
        self.errors.append(message)
    
    def load_config(self) -> bool:
        """Load and parse the asset configuration."""
        self._log_info(f"Loading asset configuration from: {self.asset_path}")
        
        if not os.path.isfile(self.asset_path):
            self._log_error(f"Asset file not found: {self.asset_path}")
            return False
        
        try:
            with open(self.asset_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            if not self.config:
                self._log_error("Asset file is empty or invalid")
                return False
                
            self._log_success("Asset configuration loaded successfully")
            return True
            
        except yaml.YAMLError as e:
            self._log_error(f"YAML parsing error: {e}")
            return False
        except Exception as e:
            self._log_error(f"Failed to load asset: {e}")
            return False
    
    def validate_structure(self) -> bool:
        """Validate the asset structure and required fields."""
        self._log_info("Validating asset structure...")
        
        if not self.config:
            self._log_error("No configuration loaded")
            return False
        
        # Required sections
        required_sections = ['connection', 'authentication', 'settings', 'data']
        for section in required_sections:
            if section not in self.config:
                self._log_error(f"Missing required section: {section}")
                return False
        
        # Validate connection section
        connection = self.config.get('connection', {})
        if not connection.get('server_url'):
            self._log_error("Missing required field: connection.server_url")
            return False
        
        # Validate URL format
        server_url = connection.get('server_url')
        try:
            parsed = urlparse(server_url)
            if not parsed.scheme or not parsed.netloc:
                self._log_error(f"Invalid server URL format: {server_url}")
                return False
            
            if parsed.scheme not in ['http', 'https']:
                self._log_warning(f"Non-HTTP(S) scheme in URL: {parsed.scheme}")
                
        except Exception:
            self._log_error(f"Failed to parse server URL: {server_url}")
            return False
        
        # Validate authentication section
        auth = self.config.get('authentication', {})
        auth_type = auth.get('type')
        if not auth_type:
            self._log_error("Missing required field: authentication.type")
            return False
        
        if auth_type not in ['none', 'basic', 'api_key', 'bearer']:
            self._log_error(f"Invalid authentication type: {auth_type}")
            return False
        
        # Validate auth-specific fields
        if auth_type == 'basic':
            if not auth.get('username') or not auth.get('password'):
                self._log_error("Basic auth requires username and password")
                return False
        elif auth_type == 'api_key':
            if not auth.get('api_key'):
                self._log_error("API key auth requires api_key field")
                return False
        elif auth_type == 'bearer':
            if not auth.get('token'):
                self._log_error("Bearer auth requires token field")
                return False
        
        # Validate index patterns
        benchmark_index = connection.get('benchmark_index')
        metadata_index = connection.get('metadata_index')
        
        if not benchmark_index:
            self._log_warning("No benchmark_index specified, using default")
        if not metadata_index:
            self._log_warning("No metadata_index specified, using default")
        
        self._log_success("Asset structure validation passed")
        return True
    
    def test_connectivity(self) -> bool:
        """Test connectivity to Elasticsearch cluster."""
        self._log_info("Testing Elasticsearch connectivity...")
        
        if not self.config:
            self._log_error("No configuration loaded")
            return False
        
        connection = self.config.get('connection', {})
        auth = self.config.get('authentication', {})
        settings = self.config.get('settings', {})
        
        server_url = connection.get('server_url')
        timeout = settings.get('timeout', 30)
        verify_ssl = settings.get('verify_ssl', True)
        
        # Prepare request parameters
        request_kwargs = {
            'timeout': timeout,
            'verify': verify_ssl
        }
        
        # Handle authentication
        auth_type = auth.get('type')
        if auth_type == 'basic':
            request_kwargs['auth'] = (auth.get('username'), auth.get('password'))
        elif auth_type == 'api_key':
            request_kwargs['headers'] = {
                'Authorization': f"ApiKey {auth.get('api_key')}"
            }
        elif auth_type == 'bearer':
            request_kwargs['headers'] = {
                'Authorization': f"Bearer {auth.get('token')}"
            }
        
        # Test cluster health endpoint
        try:
            health_url = f"{server_url.rstrip('/')}/_cluster/health"
            self._log_info(f"Testing connection to: {health_url}")
            
            response = requests.get(health_url, **request_kwargs)
            
            if response.status_code == 200:
                health_data = response.json()
                cluster_name = health_data.get('cluster_name', 'unknown')
                status = health_data.get('status', 'unknown')
                
                self._log_success(f"Connected to cluster '{cluster_name}' (status: {status})")
                
                if status == 'red':
                    self._log_warning("Cluster status is RED - some functionality may be impaired")
                
                return True
            else:
                self._log_error(f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            self._log_error("Connection refused - check server URL and network connectivity")
            return False
        except requests.exceptions.Timeout:
            self._log_error(f"Connection timeout after {timeout}s")
            return False
        except requests.exceptions.SSLError:
            self._log_error("SSL/TLS error - check certificates or try verify_ssl: false")
            return False
        except Exception as e:
            self._log_error(f"Connectivity test failed: {e}")
            return False
    
    def test_indices(self) -> bool:
        """Test access to configured indices."""
        self._log_info("Testing index accessibility...")
        
        if not self.config:
            return False
        
        connection = self.config.get('connection', {})
        auth = self.config.get('authentication', {})
        settings = self.config.get('settings', {})
        
        server_url = connection.get('server_url')
        benchmark_index = connection.get('benchmark_index', 'ripsaw-kube-burner-*')
        metadata_index = connection.get('metadata_index', 'perf_scale_ci*')
        
        # Prepare request parameters (same as connectivity test)
        request_kwargs = {
            'timeout': settings.get('timeout', 30),
            'verify': settings.get('verify_ssl', True)
        }
        
        auth_type = auth.get('type')
        if auth_type == 'basic':
            request_kwargs['auth'] = (auth.get('username'), auth.get('password'))
        elif auth_type == 'api_key':
            request_kwargs['headers'] = {
                'Authorization': f"ApiKey {auth.get('api_key')}"
            }
        elif auth_type == 'bearer':
            request_kwargs['headers'] = {
                'Authorization': f"Bearer {auth.get('token')}"
            }
        
        indices_to_test = [
            ('benchmark', benchmark_index),
            ('metadata', metadata_index)
        ]
        
        success = True
        
        for index_type, index_pattern in indices_to_test:
            try:
                # Use _cat/indices API to check if indices exist
                cat_url = f"{server_url.rstrip('/')}/_cat/indices/{index_pattern}"
                self._log_info(f"Checking {index_type} indices: {index_pattern}")
                
                response = requests.get(cat_url, **request_kwargs)
                
                if response.status_code == 200:
                    indices = response.text.strip().split('\n') if response.text.strip() else []
                    if indices and indices[0]:  # Check if any indices found
                        self._log_success(f"Found {len(indices)} {index_type} indices matching pattern")
                    else:
                        self._log_warning(f"No {index_type} indices found for pattern: {index_pattern}")
                        success = False
                else:
                    self._log_error(f"Failed to check {index_type} indices: HTTP {response.status_code}")
                    success = False
                    
            except Exception as e:
                self._log_error(f"Failed to test {index_type} indices: {e}")
                success = False
        
        return success
    
    def run_sample_query(self) -> bool:
        """Run a sample query to test data access."""
        self._log_info("Running sample query to test data access...")
        
        if not self.config:
            return False
        
        connection = self.config.get('connection', {})
        auth = self.config.get('authentication', {})
        settings = self.config.get('settings', {})
        
        server_url = connection.get('server_url')
        benchmark_index = connection.get('benchmark_index', 'ripsaw-kube-burner-*')
        
        # Prepare request parameters
        request_kwargs = {
            'timeout': settings.get('timeout', 30),
            'verify': settings.get('verify_ssl', True),
            'headers': {'Content-Type': 'application/json'}
        }
        
        auth_type = auth.get('type')
        if auth_type == 'basic':
            request_kwargs['auth'] = (auth.get('username'), auth.get('password'))
        elif auth_type == 'api_key':
            request_kwargs['headers']['Authorization'] = f"ApiKey {auth.get('api_key')}"
        elif auth_type == 'bearer':
            request_kwargs['headers']['Authorization'] = f"Bearer {auth.get('token')}"
        
        # Simple query to get one document
        query = {
            "query": {"match_all": {}},
            "size": 1
        }
        
        try:
            search_url = f"{server_url.rstrip('/')}/{benchmark_index}/_search"
            
            response = requests.post(search_url, 
                                   json=query, 
                                   **request_kwargs)
            
            if response.status_code == 200:
                result = response.json()
                total_hits = result.get('hits', {}).get('total', {})
                
                # Handle both ES 6.x and 7.x+ total format
                if isinstance(total_hits, dict):
                    count = total_hits.get('value', 0)
                else:
                    count = total_hits
                
                self._log_success(f"Sample query successful - found {count} documents")
                return True
            else:
                self._log_error(f"Sample query failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self._log_error(f"Sample query failed: {e}")
            return False
    
    def validate_all(self, skip_connectivity: bool = False) -> bool:
        """Run all validation checks."""
        self._log_info("Starting complete asset validation...")
        
        # Load configuration
        if not self.load_config():
            return False
        
        # Validate structure
        if not self.validate_structure():
            return False
        
        # Skip connectivity tests if requested
        if skip_connectivity:
            self._log_info("Skipping connectivity tests as requested")
            success = True
        else:
            # Test connectivity
            connectivity_ok = self.test_connectivity()
            
            # Test indices (only if connectivity works)
            indices_ok = True
            sample_query_ok = True
            
            if connectivity_ok:
                indices_ok = self.test_indices()
                sample_query_ok = self.run_sample_query()
            
            success = connectivity_ok and indices_ok and sample_query_ok
        
        # Print summary
        self._print_summary(success, skip_connectivity)
        
        return success and len(self.errors) == 0
    
    def _print_summary(self, success: bool, skip_connectivity: bool):
        """Print validation summary."""
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        if success and len(self.errors) == 0:
            self._log_success("All validations passed!")
        elif len(self.errors) > 0:
            self._log_error(f"Validation failed with {len(self.errors)} error(s)")
        
        if self.warnings:
            self._log_warning(f"Found {len(self.warnings)} warning(s)")
        
        if skip_connectivity:
            print(f"{Colors.YELLOW}Note: Connectivity tests were skipped{Colors.NC}")
        
        # Print configuration summary
        if self.config:
            connection = self.config.get('connection', {})
            auth = self.config.get('authentication', {})
            
            print(f"\nConfiguration Summary:")
            print(f"  Server: {connection.get('server_url', 'N/A')}")
            print(f"  Auth Type: {auth.get('type', 'N/A')}")
            print(f"  Benchmark Index: {connection.get('benchmark_index', 'default')}")
            print(f"  Metadata Index: {connection.get('metadata_index', 'default')}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Elasticsearch asset configuration for Orion Claude skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Find and validate asset automatically
  %(prog)s assets/elasticsearch-config.yaml  # Validate specific asset file
  %(prog)s --skip-connectivity               # Skip network connectivity tests
  %(prog)s --help                            # Show this help message
        """
    )
    
    parser.add_argument(
        'asset_path',
        nargs='?',
        help='Path to elasticsearch-config.yaml asset file (optional - will search common locations)'
    )
    
    parser.add_argument(
        '--skip-connectivity',
        action='store_true',
        help='Skip connectivity and index tests (only validate configuration structure)'
    )
    
    args = parser.parse_args()
    
    # Create validator and run validation
    validator = ESAssetValidator(args.asset_path)
    success = validator.validate_all(skip_connectivity=args.skip_connectivity)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()