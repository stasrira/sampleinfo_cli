import json
import click
from os import environ, path
from dotenv import load_dotenv
import requests
import csv
import pathlib

# load environment variables from files
basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.flaskenv'))
load_dotenv(path.join(basedir, '.env'))
api_server_url = environ.get('SAMPLEINFO_CLI_URL')

@click.command()
@click.option("--data-type", "-d", default="metadata_stats",
    help="\b\n"
         "Type of data to be requested. Expected values: "
         "\nmetadata_stats (no required parameters) - returns a list of the available metadata datasets, "
         "\nsampleinfo_stats (no required parameters) - returns a list of the available sampleinfo datasets, "
         "\nmetadata (requires -s or -c parameters) - returns metadata dataset for the given study_id (-s); "
         "\n                                          study_id (-s) parameter preveils center_id (-c) one - center_id will be ignored if study_id is provided;"
         "\n                                          if only center_id (-c) is provided, the process will identify the default study_id "
         "\n                                          withing the given center_id and return that data."
         "\nsampleinfo (requires -cs and -dt parameters) - returns sampleinfo dataset for the given center_ids (-cs) and dataset_type_id (-dt);"
         "\n                                               see more details in help info for -cs and -dt parameters",
)
@click.option("--study_id", "-s", default="",
    help="Study_id of the requested metadata. Used only for metadata. If omitted, "
         "center_id parameter is expected to be provided.",
)
@click.option("--center_id", "-c", default="",
    help="center_id of the requested metadata. Used only for metadata. If omitted, "
         "study_id parameter is expected to be provided.",
)
@click.option("--center_ids", "-cs", default="",
    help="center_ids of the requested samlpeinfo dataset; multiple comma delimited values can be provided. "
         "Required parameter. Used only for sampleinfo data.",
)
@click.option("--dataset_type_id", "-dt", default="",
    help="Dataset_type_id of the requested samlpeinfo dataset. Used only for sampleinfo data. If omitted, "
         "default 'manifest' value (1) will be used.",
)
@click.option("--out-file", "-o", default="",  # ./output.csv
    help="Path to csv file to store the result.",
    type=click.Path(dir_okay=False)
)
@click.option("--output-format", "-of", default="csv",
    help="Data format to be used to output received data. Expected values are: 1) csv - for comma delimited format, "
         "2) json - for json format",
)

def process(data_type, study_id, center_id, center_ids, dataset_type_id, out_file, output_format):
    # print ("data_type = {}, study_id = {}, out_file = {}".format(data_type, study_id, out_file))
    if check_data_type_value (data_type):
        api_url, err_msg = identify_api_url(data_type, study_id, center_id, center_ids, dataset_type_id)
    else:
        api_url = ''
        err_msg = 'Unexpected data_type value ({}) was provided. Run --help for the list of expected values.'\
            .format(data_type)
    if len(err_msg) == 0:
        if len(api_url) > 0:
            # access api and retrieve the data
            response = requests.get(api_url)
            # print ("data_type = {}, study_id = {}, out_file = {}".format(data_type, stu)
            # print(response.status_code)
            # json_parsed =

            output_data (response.json(), out_file, output_format)
        else:
            print ('Error: Cannot identify the database call for the given parameters.')
    else:
        # report an error
        print('Error: {}'.format(err_msg))

def check_data_type_value(data_type):
    data_type_values = ['metadata_stats', 'sampleinfo_stats', 'metadata', 'sampleinfo']
    if data_type in data_type_values:
        return True
    else:
        return False

def identify_api_url (data_type, study_id, center_id, center_ids, dataset_type_id):
    # api_server_url = environ.get('SAMPLEINFO_CLI_URL')
    error_message = ''
    out_url = None

    # if metadata stats view was requested
    if data_type == 'metadata_stats' or len(data_type.strip()) == 0:
        out_url = '{}/api/metadata/stats'.format(api_server_url)

    # if sampleinfo stats view was requested
    if data_type == 'sampleinfo_stats':
        out_url = '{}/api/sampleinfo/stats'.format(api_server_url)

    # if metadata was requested and study_id or center_id values were provided
    if data_type == 'metadata' and (len(str(study_id).strip()) > 0 or len(str(center_id).strip()) > 0):
        # if study_id is provided, center_id can be ignored
        if len(study_id.strip()) > 0:
            out_url = '{}/api/metadata/study/{}'.format(api_server_url, study_id.strip())
        if len(center_id.strip()) > 0:
            out_url = '{}/api/metadata/center/{}'.format(api_server_url, center_id.strip())
    # if out_url was not set yet, metadata was requested and study_id or center_id values were not provided
    if not out_url and data_type == 'metadata':
        # report an error since one of the parameters must be provided
        error_message = 'Missing value - "status_id" or "center_id" value is required to run the metadata query.'

    # if sampleinfo was requested and center_id and dataset_type_id values were provided
    if data_type == 'sampleinfo' and len(str(dataset_type_id).strip()) > 0 and len(str(center_ids).strip()) > 0:
        out_url = '{}/api/sampleinfo/center_datasettype/{}/{}'\
            .format(api_server_url, center_ids.strip(), dataset_type_id.strip())
    # if out_url was not set yet, sampleinfo was requested
    # and center_id value was provided while dataset_type_id was not
    if not out_url and data_type == 'sampleinfo' and len(str(center_ids).strip()) > 0:
        out_url = '{}/api/sampleinfo/dataset?center_ids={}'.format(api_server_url, center_ids.strip())
    # if out_url was not set yet, sampleinfo was requested and required parameter values were not provided report error
    if not out_url and data_type == 'sampleinfo':
        error_message = 'Missing value - "center_ids" value is required to run the sampleinfo query.'

    return out_url, error_message

def output_data (json_parsed, out_file, dataformat = None):
    if not dataformat:
        dataformat = 'csv'

    if dataformat == 'csv':
        output_data_csv (json_parsed, out_file)
    if dataformat == 'json':
        output_data_json(json_parsed, out_file)

def output_data_csv (json_parsed, out_file):
    # check if output to file was requested
    out_to_file = False
    if len(out_file.strip()) > 0:
        out_to_file = True
    else:
        out_file = '___temp_file___.csv'

    # if out_to_file:
    # open file for output; newline='' was added to avoid blank lines between the rows (for Python3)
    result_file = open(out_file, 'w', newline='')
    csv_writer = csv.writer(result_file)
    count = 0

    if 'data' in json_parsed:
        for row in json_parsed['data']:
            if count == 0:
                # Writing headers of CSV file
                header = row.keys()
                csv_writer.writerow(header)
                # output_function (header)
                count += 1

            # Writing data of CSV file
            csv_writer.writerow(row.values())
            # output_function(row.values())
            # if out_to_file:
            #     csv_writer.writerow(row.values())
            # else:
            #     print(','.join(str(val) for val in row.values()))
    else:
        print(json_parsed)

    # close file, if that was opened
    result_file.close()

    if not out_to_file:
        # if output file was not provided, read the created temp file, print the output and drop the file afterword
        result_file = open(out_file, 'r')
        for line in result_file.readlines():
            print(line.strip())
        result_file.close()
        # delete file
        result_file = pathlib.Path(out_file)
        result_file.unlink()

def output_data_json (json_parsed, out_file):
    # check if output to file was requested
    out_to_file = False
    if len(out_file.strip()) > 0:
        out_to_file = True

    if out_to_file:
        # open file for output; newline='' was added to avoid blank lines between the rows (for Python3)
        result_file = open(out_file, 'a', newline='')

        if 'data' in json_parsed:
            result_file.write(json.dumps(json_parsed['data'], indent = 4))
        else:
            print(json_parsed)
        # close file, if that was opened
        result_file.close()

    if not out_to_file:
        # if output file was not provided
        if 'data' in json_parsed:
            print(json.dumps(json_parsed['data']))
        else:
            print(json_parsed)

if __name__ =="__main__":
    process()