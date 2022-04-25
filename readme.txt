# Steps to produce and executable file for this tool:
# 1. Run the following command to produce an executable file. It will be created in the "dist" folder in root of the project
# pyinstaller -F sampleinfo.py
# 2. Copy "configs" folder with its content (main_config.yaml file) to the "dist" folder, since the code relies on the configuration file
# 3. Content of the "dist" folder is ready for distribution.
# 3.1 Paramters of the main_config.yaml file SAMPLEINFO_CLI_URL should be updated in accordance with the environment it is being set to