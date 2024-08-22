import json
import argparse
import re
import sys

def print_logo():
    logo = """
 .       . .       . .    .       . .    .    .       . .       . .    
 |`+. .+'|=|`+. .+'|=|`+. |`+. .+'|=|`+.=|`+. |`+. .+'|=|`+. .+'|=|`+. 
 |  | |  | `+.| |  | `+ | |  | |.+' |  | `+.| |  | |  | |  | |  | `+ | 
 |  | |  | .    |  |  | | |  |      |  |      |  | |  | |  | |  |  | | 
 |  | |  | |`+. |  |  | | |  |      |  |      |  | |  | |  | |  |  | | 
 |  | |  | `. | |  |  | | |  |      |  |      |  | |  | |  | |  |  | | 
 |  | |  | .+ | |  |  | | |  |      |  |      |  | |  | |  | |  |  | | 
 |.+' `+.|=|.+' `+.|  |.| |.+'      |.+'      |.+' `+.|=|.+' `+.|  |.| 
                Ignition.py v0.2 - Author: 10N351R
"""
    
    print(logo)
    
# Print logo and author
print_logo()

# Set up argument parsing
parser = argparse.ArgumentParser(description='Generate curl commands from Swagger/OpenAPI JSON.')
parser.add_argument('-t', '--target', required=True, help='The base URL for the target (e.g., http://localhost)')
parser.add_argument('-p', '--proxy', help='Proxy in the format domain:port (e.g., localhost:9000)')
parser.add_argument('-H', '--headers', nargs='*', help='Optional headers to include in the request (e.g., "Authorization: Bearer token")')
parser.add_argument('-f', '--file', required=True, help='Path to the Swagger/OpenAPI JSON file')
parser.add_argument('-c', '--canary', help='Optional canary string to inject into placeholders and empty fields')
parser.add_argument('--canary-endpoint', help='String to replace placeholders in the endpoint URL')
parser.add_argument('--canary-body', help='String to replace empty strings in the request body')
parser.add_argument('-o', '--out', help='Optional output file to save the generated curl commands')

args = parser.parse_args()

# Check for mutually exclusive arguments
if args.canary and (args.canary_endpoint or args.canary_body):
    print("Error: The --canary option is mutually exclusive with --canary-endpoint and --canary-body.")
    parser.print_help()
    sys.exit(1)

# Load the Swagger/OpenAPI JSON file
with open(args.file) as f:
    swagger = json.load(f)

# Determine if the file is OpenAPI 3.0 or Swagger 2.0
is_openapi_3 = swagger.get('openapi', '').startswith('3.0')
if is_openapi_3:
    # For OpenAPI 3.0, use the first server URL and adjust it to fit the target base URL
    base_url = swagger['servers'][0]['url']
    base_path = '/'.join(base_url.split('://')[1].split('/')[1:])  # Extract everything after the top-level domain
    base_url = f"{args.target}/{base_path}"
else:
    # For Swagger 2.0, construct the base URL from host and basePath
    base_url = f"{args.target}{swagger['basePath']}"

# Get schema definitions (Swagger 2.0) or components/schemas (OpenAPI 3.0)
definitions = swagger.get('definitions', {}) if not is_openapi_3 else swagger.get('components', {}).get('schemas', {})

# Function to replace placeholders in URL with canary string
def replace_placeholders(url, canary_string):
    return re.sub(r'\{[^\}]*\}', canary_string, url)

# Generate curl commands for each endpoint
def generate_curl_commands(paths):
    commands = []
    for path, methods in paths.items():
        # Handle endpoint canary string if specified
        if args.canary_endpoint:
            full_url = replace_placeholders(f"{base_url}{path}", args.canary_endpoint)
        elif args.canary:
            full_url = replace_placeholders(f"{base_url}{path}", args.canary)
        else:
            full_url = f"{base_url}{path}"
        
        for method, details in methods.items():
            command = f"curl -X {method.upper()} \"{full_url}\""
            
            # Add proxy if specified
            if args.proxy:
                command += f" -x {args.proxy}"
            
            # Add optional headers if specified
            if args.headers:
                for header in args.headers:
                    command += f" -H \"{header}\""

            # Add Content-Type header and body if applicable
            if method.lower() == 'post':
                command += " -H \"Content-Type: application/json\""
                
                # Add request body for POST requests
                if 'requestBody' in details:
                    content = details['requestBody'].get('content', {})
                    body = {}
                    if 'application/json' in content:
                        schema_ref = content['application/json'].get('schema', {}).get('$ref', None)
                        if schema_ref:
                            definition = definitions.get(schema_ref.split('/')[-1], {})
                            if definition:
                                body = {
                                    key: (args.canary_body if args.canary_body else value.get('example', ''))
                                    for key, value in definition.get('properties', {}).items()
                                }
                    if body:
                        if args.canary_body:
                            body = {k: args.canary_body for k in body}
                        elif args.canary:
                            body = {k: args.canary for k in body}
                        command += f" -d '{json.dumps(body)}'"
            
            commands.append(command)
    return commands

# Identify the number of API endpoints
num_endpoints = len(swagger['paths'])
print(f"[+] Parsed {num_endpoints} endpoints from {args.file}")
print()

# Generate commands
curl_commands = generate_curl_commands(swagger['paths'])

# Print commands to the console
for command in curl_commands:
    print(command)

# Write commands to file and print message if --out is specified
if args.out:
    with open(args.out, 'w') as f:
        for command in curl_commands:
            f.write(command + '\n')
    print(f"\n[+] Commands have been saved to \"{args.out}\"")
