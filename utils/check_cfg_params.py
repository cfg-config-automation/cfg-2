import configparser
import argparse
import logging
import sys

def read_range(value) -> tuple:
    try:
        range_str = value.replace("RANGE", "").replace("range", "").strip("[]")
        start, end = map(int, range_str.split(","))
        return start, end
    except Exception as e:
        print(f"Invalid range format: '{value}', error: {e}")
        return None


def read_cfg_to_dict(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return {section: dict(config.items(section)) for section in config.sections()}


def validate_config(actual_dict, expected_dict, cfg_file_path):
    output = set()
    flag = 0
    filename = cfg_file_path.split('/')[-1]
    for section, parameters in expected_dict.items():
        for key, value in parameters.items():
            if value.upper() == "MUST_EXIST":
                if section not in actual_dict:
                    output.add(f"MUST: [{section}] section should be present in {filename}")
                    flag = 1
                    continue

                if key not in actual_dict[section]:
                    output.add(f"MUST: '{key}' should be present in section [{section}] in {filename}")
                    flag = 1

            elif value.upper() == "SHOULD_NOT_BE_PRESENT":
                if section in actual_dict:
                    if key in actual_dict[section]:
                        output.add(f"NOT_BE: '{key}' should NOT be in section [{section}] in {filename}")
                        flag = 1

            elif value.upper().startswith("RANGE"):
                if section in actual_dict:
                    if key in actual_dict[section]:
                        my_range = read_range(value)
                        try:
                            actual_val = int(actual_dict[section][key])
                            if my_range and actual_val not in range(my_range[0], my_range[1] + 1):
                                output.add(f"COUNT: Value of '{key}' in [{section}] of {filename} not in range {my_range}")
                                flag = 1
                        except ValueError:
                            output.add(f"ERROR: Value of '{key}' in [{section}] of {filename} is not an integer")
                            flag = 1

            else:
                if section in actual_dict:
                    if key in actual_dict[section]:
                        if actual_dict[section][key] != value:
                            output.add(f"MISSMATCH: Value '{key}' in section [{section}] is '{actual_dict[section][key]}' in '{filename}' expected '{value}'")
                            flag = 1
                        continue

    return output, flag

if __name__ == "__main__":
    logger = logging.getLogger("validate")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    parser = argparse.ArgumentParser(description="Validate configuration files")
    parser.add_argument("--input_files", required=True, help="Comma-separated list of input config files")
    parser.add_argument("--default_file", required=True, help="Path to expected configuration file")

    args = parser.parse_args()
    actual_files = args.input_files.split(",")
    expected_config = read_cfg_to_dict(args.default_file)
    overall_flag = 0
    for file in actual_files:
        actual_config = read_cfg_to_dict(file)
        errors, flag = validate_config(actual_dict=actual_config,
                                              expected_dict=expected_config,
                                              cfg_file_path=file)
        if errors and flag == 1:
            for er in errors:
                logger.error(er)
            overall_flag = 1

        else:
            logger.info(f"All parameters in '{file}' match the expected configuration.")
    overall_flag = max(overall_flag, flag)
if overall_flag == 1:
    logger.error("Validation failed. Overall Execution flag: 1")
    sys.exit(1)
else:
    logger.info("Validation successful. Overall Execution flag: 0")
    sys.exit(0)

