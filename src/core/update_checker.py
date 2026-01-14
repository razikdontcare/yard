"""GitHub update checker with caching."""

import json
import os
import time
import urllib.request
import urllib.error
from packaging import version


class UpdateChecker:
    """Checks for application updates on GitHub."""
    
    def __init__(self, current_version, cache_file, repo_owner, repo_name):
        """
        Initialize update checker.
        
        Args:
            current_version: Current app version string
            cache_file: Path to cache file
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
        """
        self.current_version = current_version
        self.cache_file = cache_file
        self.repo_owner = repo_owner
        self.repo_name = repo_name
    
    def check(self, force=False):
        """
        Check for updates.
        
        Args:
            force: If True, bypass cache and always check GitHub API
        
        Returns:
            dict or None: {'version': str, 'url': str} if update available, None otherwise
        """
        try:
            latest_version = None
            download_url = None
            
            # Check cache (don't check more than once per day) unless forced
            if not force and os.path.exists(self.cache_file):
                try:
                    with open(self.cache_file, 'r') as f:
                        cache = json.load(f)
                        if time.time() - cache.get('last_check', 0) < 86400:  # 24 hours
                            latest_version = cache.get('latest')
                            download_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/releases/tag/v{latest_version}"
                except Exception:
                    pass
            
            # Fetch from API if not cached or forced
            if latest_version is None:
                url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Yard-UpdateChecker')
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read())
                    latest_version = data['tag_name'].lstrip('v')
                    download_url = data['html_url']
                    
                    # Save cache
                    with open(self.cache_file, 'w') as f:
                        json.dump({'last_check': time.time(), 'latest': latest_version}, f)
            
            # Compare versions
            if version.parse(latest_version) > version.parse(self.current_version):
                return {'version': latest_version, 'url': download_url}
            
            return None
            
        except (urllib.error.URLError, Exception):
            return None
