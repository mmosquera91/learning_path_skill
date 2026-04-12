#!/usr/bin/env python3
"""
URL Validator for learning-path skill.
Validates URLs against tier system and checks HTTP status.
Usage: python3 validate_urls.py < urls.json
         python3 validate_urls.py --check "https://..."
"""
import re
import sys
import json
import subprocess
import argparse
from urllib.parse import urlparse

# URL patterns by tier - GENERIC patterns that work across topics
TIER_PATTERNS = {
    1: [  # Highest reliability - interactive learning platforms
        # Generic interactive lesson patterns
        (r'/lessons?/[\w-]+$', "interactive lesson"),
        (r'/learn(/|#|/\d+|ing-paths?)[\w/#]*$', "learn platform"),
        (r'/practice/[\w/-]+', "practice exercises"),
        (r'/exercises?/[\w/-]+', "exercises"),
        (r'/tutorials?/interactive[\w/-]*', "interactive tutorial"),
        (r'exercism\.org/tracks?/[\w/-]+', "exercism track"),
        (r'codecademy\.com/learn/[\w/-]+', "codecademy"),
        (r'duolingo\.com/lesson|duolingo\.com/course', "duolingo"),
        (r'brilliant\.org/courses?/[\w/-]+', "brilliant course"),
        (r'leetcode\.com/studyplan/[\w/-]+', "leetcode study plan"),
    ],
    2: [  # Official courses and docs
        (r'coursera\.org/learn/[\w-]+', "coursera"),
        (r'edx\.org/learn/[\w-]+', "edx"),
        (r'khanacademy\.org/[\w/-]+', "khan academy"),
        (r'freecodecamp\.org/learn/[\w/-]+', "freecodecamp"),
        (r'udemy\.com/course/[\w-]+', "udemy course"),
        (r'udacity\.com/course/[\w-]+', "udacity course"),
        (r'/docs(?:/[\w-]+)+', "official documentation"),
    ],
    3: [  # YouTube (single videos only)
        # Special handling - no playlists allowed
    ],
    4: [  # Reference
        (r'wikipedia\.org/wiki/[\w_]+', "wikipedia"),
        (r'github\.com/[\w-]+/[\w-]+/(?:wiki|blob|tree)', "github wiki/docs"),
        (r'medium\.com/@[\w-]+/[\w-]+', "medium article"),
        (r'dev\.to/[\w-]+/[\w-]+', "dev.to article"),
    ]
}

def classify_url(url):
    """Classify URL by tier. Returns (tier, type_name) or (None, error_reason)."""
    url = url.strip()
    
    if not url.startswith(('http://', 'https://')):
        return (None, "Not a valid HTTP URL")
    
    # Special handling for YouTube - REJECT PLAYLISTS
    if 'youtube.com' in url or 'youtu.be' in url:
        if '&list=' in url or 'playlist?' in url:
            return (None, "YouTube PLAYLIST - not allowed")
        if re.match(r'https?://(www\.)?(youtube\.com/watch\?v=[\w-]+(&[^&]*)?|youtu\.be/[\w-]+)', url):
            return (3, "YouTube single video")
        return (None, "Invalid YouTube URL format")
    
    # Check against tier patterns
    # Two-pass: specific (domain-anchored) patterns first across all tiers,
    # then generic (path-based) patterns. This prevents a generic tier 1 pattern
    # from shadowing a specific tier 2 domain pattern (e.g., coursera.org/learn).
    for tier in [1, 2, 4]:  # Skip 3 (handled above)
        for pattern, type_name in TIER_PATTERNS[tier]:
            if '.' in pattern and re.search(pattern, url):
                return (tier, type_name)
    for tier in [1, 2, 4]:  # Skip 3 (handled above)
        for pattern, type_name in TIER_PATTERNS[tier]:
            if '.' not in pattern and re.search(pattern, url):
                return (tier, type_name)

    return (None, "Unknown/untrusted domain")

def check_http_status(url, timeout=10):
    """Check HTTP status of URL. Returns (status_code, is_ok)."""
    try:
        result = subprocess.run(
            ['curl', '-sI', '-o', '/dev/null', '-w', '%{http_code}', 
             '--max-time', str(timeout), '-L', url],
            capture_output=True,
            text=True,
            timeout=timeout + 5
        )
        status = result.stdout.strip()
        is_ok = status.startswith(('2', '3'))
        return (status, is_ok)
    except subprocess.TimeoutExpired:
        return ("TIMEOUT", False)
    except Exception as e:
        return (f"ERROR: {e}", False)

def validate_single(url, check_http=False):
    """Validate a single URL. Returns dict with results."""
    tier, type_info = classify_url(url)
    
    result = {
        'url': url,
        'tier': tier,
        'type': type_info,
        'valid': tier is not None
    }
    
    if check_http and tier in [1, 2]:  # Only check HTTP for reliable tiers
        status, is_ok = check_http_status(url)
        result['http_status'] = status
        result['http_ok'] = is_ok
    
    return result

def validate_syllabus(syllabus_data, check_http=False):
    """Validate all URLs in a syllabus. Returns report."""
    report = {
        'total_resources': 0,
        'by_tier': {1: [], 2: [], 3: [], 4: [], 'invalid': []},
        'modules': []
    }
    
    for module in syllabus_data.get('modules', []):
        module_report = {
            'title': module.get('title'),
            'resources': [],
            'tier_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 'invalid': 0}
        }
        
        for resource in module.get('resources', []):
            url = resource.get('url', '')
            report['total_resources'] += 1
            
            result = validate_single(url, check_http=check_http)
            module_report['resources'].append(result)
            
            tier_key = result['tier'] if result['tier'] else 'invalid'
            module_report['tier_distribution'][tier_key] += 1
            report['by_tier'][tier_key].append(result)
        
        # Check module balance
        total = sum(module_report['tier_distribution'].values())
        tier1_count = module_report['tier_distribution'][1]
        tier1_pct = (tier1_count / total * 100) if total > 0 else 0
        
        module_report['balance_ok'] = tier1_pct >= 50
        module_report['tier1_percentage'] = tier1_pct
        
        report['modules'].append(module_report)
    
    return report

def print_report(report):
    """Print validation report in readable format."""
    print("=" * 60)
    print(f"URL VALIDATION REPORT")
    print("=" * 60)
    print(f"\nTotal resources: {report['total_resources']}")
    print(f"\nBy tier:")
    print(f"  TIER 1 (⭐⭐⭐⭐⭐ Interactive): {len(report['by_tier'][1])}")
    print(f"  TIER 2 (⭐⭐⭐⭐ Official): {len(report['by_tier'][2])}")
    print(f"  TIER 3 (⭐⭐ YouTube): {len(report['by_tier'][3])}")
    print(f"  TIER 4 (⭐⭐ Reference): {len(report['by_tier'][4])}")
    print(f"  INVALID: {len(report['by_tier']['invalid'])}")
    
    print(f"\n{'='*60}")
    print("MODULE BREAKDOWN")
    print("=" * 60)
    
    for mod in report['modules']:
        status = "✅" if mod['balance_ok'] else "❌"
        print(f"\n{status} {mod['title']}")
        print(f"   TIER 1: {mod['tier_distribution'][1]}, "
              f"TIER 2: {mod['tier_distribution'][2]}, "
              f"TIER 3: {mod['tier_distribution'][3]}, "
              f"TIER 4: {mod['tier_distribution'][4]}")
        print(f"   TIER 1 percentage: {mod['tier1_percentage']:.1f}%")
        
        # Show invalid resources
        for res in mod['resources']:
            if not res['valid']:
                print(f"   ❌ INVALID: {res['url']}")
                print(f"      Reason: {res['type']}")
            elif 'http_ok' in res and not res['http_ok']:
                print(f"   ⚠️  HTTP {res['http_status']}: {res['url']}")

def main():
    parser = argparse.ArgumentParser(description='Validate URLs for learning-path skill')
    parser.add_argument('--check', '-c', help='Check single URL')
    parser.add_argument('--file', '-f', help='Validate JSON syllabus file')
    parser.add_argument('--http', action='store_true', help='Also check HTTP status')
    args = parser.parse_args()
    
    if args.check:
        result = validate_single(args.check, check_http=args.http)
        tier_stars = "⭐" * (result['tier'] if result['tier'] else 0)
        status = "✅ VALID" if result['valid'] else "❌ INVALID"
        print(f"{status} - TIER {result['tier']} {tier_stars}")
        print(f"  URL: {result['url']}")
        print(f"  Type: {result['type']}")
        if 'http_status' in result:
            http_status = "✅" if result['http_ok'] else "❌"
            print(f"  HTTP: {http_status} {result['http_status']}")
    
    elif args.file:
        with open(args.file) as f:
            data = json.load(f)
        report = validate_syllabus(data, check_http=args.http)
        print_report(report)
    
    else:
        # Read from stdin
        try:
            data = json.load(sys.stdin)
            report = validate_syllabus(data, check_http=args.http)
            print_report(report)
        except json.JSONDecodeError:
            print("Error: Invalid JSON. Provide syllabus JSON via stdin or use --file")
            sys.exit(1)

if __name__ == "__main__":
    main()
