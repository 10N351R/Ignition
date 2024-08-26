import argparse
import subprocess
import itertools
import time
import shlex
import logging
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

print("Unnamed API Fuzzer - Author: 10N351R")

class APIFuzzer:
    def __init__(self, target_file, wordlists, exclude_codes=None, exclude_lengths=None, threads=10, timeout=30):
        self.target_file = target_file
        self.wordlists = wordlists
        self.exclude_codes = exclude_codes or []
        self.exclude_lengths = exclude_lengths or []
        self.threads = threads
        self.timeout = timeout
        self.targets = self.load_targets()
        self.total_requests = len(self.targets) * len(self.generate_combinations())
        self.start_time = time.time()
        self.start_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"Fuzzer started at {self.start_timestamp}")

    def load_targets(self):
        """Load and return curl commands from the target file."""
        with open(self.target_file, 'r') as file:
            return [line.strip() for line in file if line.strip()]

    def generate_combinations(self):
        """Generate all possible combinations of wordlists for fuzzing."""
        return list(itertools.product(*self.wordlists))

    def parse_curl_command(self, command):
        """Parse the curl command into its components."""
        parsed_command = shlex.split(command)
        return parsed_command

    def execute_request(self, command):
        """Execute a single curl command and capture the response."""
        start_time = time.time()
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=self.timeout)
            response_time = time.time() - start_time
            response_length = len(result.stdout)
            response_code = self.extract_response_code(result.stderr)
            
            if (response_code not in self.exclude_codes and
                response_length not in self.exclude_lengths):
                result_data = {
                    "command": ' '.join(command),
                    "status_code": response_code,
                    "response_length": f"{response_length} bytes",
                    "response_time": f"{response_time:.2f}s"
                }
                logging.info(result_data)
                return result_data
        except subprocess.TimeoutExpired:
            logging.error(f"[-] Command: {' '.join(command)}, Error: Timeout")
        except subprocess.CalledProcessError as e:
            logging.error(f"[-] Command: {' '.join(command)}, Error: {e}")
        except Exception as e:
            logging.error(f"[-] Command: {' '.join(command)}, Error: {e}")
        return None

    def extract_response_code(self, stderr_output):
        """Extract HTTP response code from curl stderr output."""
        for line in stderr_output.splitlines():
            if "HTTP" in line and "200" <= line[-3:] <= "599":
                return int(line[-3:])
        return 0

    def fuzz(self, target, combination):
        """Fuzz a single API endpoint."""
        command = target
        for i, fuzz_part in enumerate(combination):
            placeholder = f"FUZZ{i+1}"
            command = command.replace(placeholder, fuzz_part)

        parsed_command = self.parse_curl_command(command)
        return self.execute_request(parsed_command)

    def run(self):
        """Run the fuzzer across all targets and wordlist combinations."""
        results = []
        combinations = self.generate_combinations()
        completed_requests = 0

        print(f"Fuzzer started at {self.start_timestamp}")

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            for target in self.targets:
                for combination in combinations:
                    futures.append(executor.submit(self.fuzz, target, combination))
            
            for future in as_completed(futures):
                result = future.result()
                completed_requests += 1
                elapsed_time = time.time() - self.start_time
                percent_complete = (completed_requests / self.total_requests) * 100
                print(f"\rProgress: {percent_complete:.2f}% | Elapsed Time: {elapsed_time:.2f}s", end='')
                if result:
                    results.append(result)

        print()  # Move to the next line after completion
        return results


def load_wordlist(file_path):
    """Load a wordlist from a file."""
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A multi-endpoint API fuzzer.")
    parser.add_argument("--target-file", required=True, help="File containing curl commands to fuzz.")
    parser.add_argument("--f1w", help="Wordlist for FUZZ1.")
    parser.add_argument("--f2w", help="Wordlist for FUZZ2.")
    parser.add_argument("--f3w", help="Wordlist for FUZZ3.")
    parser.add_argument("--f4w", help="Wordlist for FUZZ4.")
    parser.add_argument("--f5w", help="Wordlist for FUZZ5.")
    parser.add_argument("--f6w", help="Wordlist for FUZZ6.")
    parser.add_argument("--f7w", help="Wordlist for FUZZ7.")
    parser.add_argument("--f8w", help="Wordlist for FUZZ8.")
    parser.add_argument("--f9w", help="Wordlist for FUZZ9.")
    parser.add_argument("--exclude-code", nargs='*', type=int, default=[404, 403], help="HTTP status codes to exclude.")
    parser.add_argument("--exclude-length", nargs='*', type=int, default=[0], help="Response lengths to exclude.")
    parser.add_argument("--threads", type=int, default=10, help="Number of concurrent threads.")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout for each request in seconds.")
    parser.add_argument("--log-file", default="fuzzer.log", help="File to log results and errors.")
    parser.add_argument("--out", help="File to save the results in JSON format.")

    args = parser.parse_args()

    logging.basicConfig(filename=args.log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    wordlists = []
    for i in range(1, 10):
        wordlist_attr = getattr(args, f'f{i}w')
        if wordlist_attr:
            wordlists.append(load_wordlist(wordlist_attr))

    fuzzer = APIFuzzer(
        target_file=args.target_file,
        wordlists=wordlists,
        exclude_codes=args.exclude_code,
        exclude_lengths=args.exclude_length,
        threads=args.threads,
        timeout=args.timeout
    )
    results = fuzzer.run()

    # Print results to the screen
    for result in results:
        print(result)

    if args.out:
        # Save results to the specified output file
        with open(args.out, 'w') as out_file:
            json.dump(results, out_file, indent=4)
        print(f"Results saved to {args.out}")
