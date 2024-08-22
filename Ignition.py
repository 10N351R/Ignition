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
		Ignition.py v0.1 - Author: 10N351R
"""
    
    print(logo)
    
# Print logo and author
print_logo()

# Set up argument parsing
parser = argparse.ArgumentParser(description='Generate curl commands from Swagger JSON.')
parser.add_argument('-t', '--target', required=True, help='The base URL for the target')
parser.add_argument('-p', '--proxy', help='Proxy in the format domain:port (e.g., localhost:9000)')
parser.add_argument('-H', '--headers', nargs='*', help='Optional headers to include in the request (e.g., "Authorization: Bearer token")')
parser.add_argument('-f', '--file', required=True, help='Path to the Swagger JSON file')
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

# Load the Swagger JSON file
with open(args.file) as f:
    swagger = json.load(f)

# Extract base path and host
base_url = f"{args.target}{swagger['basePath']}"

# Get definitions from Swagger JSON
definitions = swagger.get('definitions', {})

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
                if 'parameters' in details:
                    body = {}
                    for param in details['parameters']:
                        if param['in'] == 'body':
                            schema_ref = param.get('schema', {}).get('$ref', None)
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
    print(f"\nCommands have been written to \"{args.out}\"")
