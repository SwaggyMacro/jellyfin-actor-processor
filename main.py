import argparse
import shutil
import sys
import time
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

TERMINAL_WIDTH = shutil.get_terminal_size().columns

# ANSI Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class ActorProcessor:
    def __init__(self, api_url: str, api_key: str, max_retries: int = 3, max_workers: int = 10, timeout: int = 30):
        """Initialize the ActorProcessor with API credentials."""
        self.api_url = api_url.rstrip('/')
        if not self.api_url.endswith('/emby'):
            self.api_url += '/emby'
        self.api_key = api_key
        self.session = requests.Session()
        self.user_ids = self.get_uids()
        self.user_id = self.user_ids[0] if self.user_ids else None
        self.max_retries = max_retries
        self.max_workers = max_workers
        self.timeout = timeout

        if not self.user_id:
            print(f"{RED}✗{RESET} No user IDs found.")
            sys.exit(1)

    def get_uids(self) -> List[str]:
        """Retrieve user IDs from the server."""
        user_ids = []
        us = requests.get(f"{self.api_url}/Users?api_key={self.api_key}").json()
        for u in us:
            user_ids.append(u["Id"])
        return user_ids

    def calculate_speed(self, content_length: int, response_time: float) -> str:
        """Calculate and format network speed."""
        if response_time == 0:
            return f"{RED}N/A{RESET}"
        speed_mbps = (content_length * 8) / (response_time / 1000) / 1_000_000
        color = GREEN if speed_mbps > 10 else YELLOW if speed_mbps > 5 else RED
        return f"{color}{speed_mbps:.2f} Mbps{RESET}"

    def check_server_connectivity(self) -> bool:
        """Check if the server is reachable using requests."""
        try:
            start_time = time.time()
            response = self.session.get(
                f"{self.api_url}/System/Info/Public",
                timeout=11
            )
            response_time = (time.time() - start_time) * 1000
            speed = self.calculate_speed(len(response.content), response_time)
            
            if response.status_code == 200:
                print(f"{GREEN}✓{RESET} Server is reachable (Response time: {BLUE}{response_time:.2f}ms{RESET}, Speed: {speed})")
                return True
            else:
                print(f"{RED}✗{RESET} Server returned status code {RED}{response.status_code}{RESET}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"{RED}✗{RESET} Connection error: {str(e)}")
            return False

    def fetch_person_data(self, force : bool = False) -> Optional[Dict]:
        """Fetch person data from the jellyfin server."""
        try:
            start_time = time.time()
            response = self.session.get(
                f"{self.api_url}/Persons",
                params={"api_key": self.api_key, "enableImages": "false" if force else "true"},
                timeout=self.timeout
            )
            response_time = (time.time() - start_time) * 1000
            speed = self.calculate_speed(len(response.content), response_time)
            
            response.raise_for_status()
            print(f"\033[K{GREEN}✓{RESET} Retrieved person data (Response time: {BLUE}{response_time:.2f}ms{RESET}, Speed: {speed})")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"{RED}✗{RESET} Failed to retrieve person data: {str(e)}")
            return None

    def process_persons(self, force: bool = False):
        """Process persons based on the force flag."""
        person_data = self.fetch_person_data(force)
        if not person_data:
            return

        total_persons = len(person_data.get('Items', []))
        print(f"{BLUE}ℹ{RESET} Total persons: {total_persons}")

        persons_to_process = []
        if force:
            persons_to_process = person_data['Items']
        else:
            persons_to_process = [item for item in person_data['Items'] 
                                if not item.get('ImageTags')]

        if not persons_to_process:
            print(f"{YELLOW}⚠{RESET} No persons to process.")
            return

        self._process_person_ids(persons_to_process)

    def _process_person_ids(self, persons: List[Dict]):
        """Process each person with progress tracking."""
        total = len(persons)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._process_person, person, idx, total): person for idx, person in enumerate(persons, 1)}
            
            for future in as_completed(futures):
                if future.exception():
                    print(f"{RED}✗{RESET} Error processing person: {future.exception()}")

    def _process_person(self, person: Dict, idx: int, total: int):
        """Process a single person with retries."""
        person_id = person['Id']
        person_name = person['Name']
        retry_count = 0
        consecutive_errors = 0
        
        while retry_count <= self.max_retries:
            try:
                start_time = time.time()
                response = self.session.get(
                    f"{self.api_url.replace('/emby', '')}/Users/{self.user_id}/Items/{person_id}",
                    params={"api_key": self.api_key},
                    timeout=5
                )
                response_time = (time.time() - start_time) * 1000
                speed = self.calculate_speed(len(response.content), response_time)
                
                status_emoji = f"{GREEN}✓{RESET}" if response.status_code == 200 else f"{RED}✗{RESET}"
                retry_info = f" (Retry {retry_count}/{self.max_retries})" if retry_count > 0 else ""
                status = f"{status_emoji} Processing {idx}/{total} - ID: {BLUE}{person_id}{RESET} - Response time: {response_time:.2f}ms, Speed: {speed}{retry_info} - (Name: {person_name})"
                
                print(f"\r{' ' * TERMINAL_WIDTH}", end='', flush=True)
                print(f"\r{status}", end='', flush=True)
                
                if response.status_code == 200:
                    consecutive_errors = 0
                    break
                else:
                    retry_count += 1
                    if retry_count <= self.max_retries:
                        print(f"\n{YELLOW}⚠{RESET} Request failed (Status: {response.status_code}). Retrying ({retry_count}/{self.max_retries})...")
                        time.sleep(0.5)
                    
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count <= self.max_retries:
                    print(f"\n{YELLOW}⚠{RESET} Request error: {str(e)}. Retrying ({retry_count}/{self.max_retries})...")
                    time.sleep(0.5)
                else:
                    consecutive_errors += 1
                    print(f"\n{RED}✗{RESET} Failed after {self.max_retries} retries: {str(e)}")
                    
        if consecutive_errors >= 10:
            print(f"\n{RED}⚠{RESET} Too many consecutive errors. Stopping.")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Jellyfin Actor Processor")
    parser.add_argument("-url", "--url", required=True, help="Jellyfin server URL")
    parser.add_argument("-key", "--api-key", required=True, help="Jellyfin API key")
    parser.add_argument("-f", "--force", action="store_true", help="Process all persons")
    parser.add_argument("-r", "--retries", type=int, default=3, help="Maximum number of retries for failed requests")
    parser.add_argument("-w", "--workers", type=int, default=10, help="Maximum number of parallel workers")
    parser.add_argument("-t", "--timeout", type=int, default=30, help="Timeout in seconds for fetching person data (default: 30)")
    args = parser.parse_args()

    print(f"{BLUE}ℹ{RESET} Jellyfin Actor Processor")
    print(f"{BLUE}ℹ{RESET} Server URL: {args.url}")
    print(f"{BLUE}ℹ{RESET} API Key: {args.api_key}")
    print(f"{BLUE}ℹ{RESET} Force: {args.force}")
    print(f"{BLUE}ℹ{RESET} Retries: {args.retries}")
    print(f"{BLUE}ℹ{RESET} Workers: {args.workers}")
    print(f"{BLUE}ℹ{RESET} Timeout: {args.timeout}s")

    processor = ActorProcessor(args.url, args.api_key, args.retries, args.workers, args.timeout)
    
    if not processor.check_server_connectivity():
        sys.exit(1)
        
    processor.process_persons(args.force)

if __name__ == "__main__":
    main()
