# Ignition.py
Author: 10N351R


**Ignition.py** is a Python script designed to parse OpenAPI (Swagger) documentation and convert it into cURL requests. Originally developed to streamline the creation of test cases for API fuzzing campaigns, and eliminates the need for manual API endpoint request construction.

## Usage 
Ignition.py can be executed like this

`python Ignition.py --target [TARGET URL] --file [FILE.json]`

### Flags
| Flag              | Shorthand | Description                                         |
|-----------------------|-----------|-----------------------------------------------------|
| `--target`            | `-t`      | The base URL for the target (e.g., http://localhost) |
| `--proxy`             | `-p`      | Optional proxy the traffic to a domain:port (e.g., localhost:9000) |
| `--headers`           | `-H`      | Optional headers to include in the request (e.g., "Authorization: Bearer token") |
| `--file`              | `-f`      | Path to the OpenAPI (Swagger) JSON file              |
| `--canary`            | `-c`      | Optional canary string to inject into placeholders and empty fields |
| `--canary-endpoint`   |           | Optional String to replace placeholders in the endpoint URL |
| `--canary-body`       |           | Optional String to replace empty strings in the request body |
| `--out`               | `-o`      | Optional output file to save the generated curl commands |


## Output
![alt text](https://github.com/10N351R/Ignition.py/blob/main/Images/Ignition_output.png)

## Disclaimer
**Ethical Use:** Ignition.py is provided for educational and lawful purposes only. The author is not responsible for any misuse or damaged caused by this tool. By using this tool, you agree to use it ethically and comply with all applicable laws and regulations. Unauthorized use of this tool is strictly prohibited and may result in severe legal consequences.

**Use Of Artificial Intelligence:** This tool was developed with the assistance of Artificial Intelligence (AI), and contains portions of code generated using OpenAI's ChatGPT, an AI language model.
