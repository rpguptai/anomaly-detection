#!/usr/bin/python
# -*- coding: utf-8 -*-
# To run : python extract_to_csv.py -h http://localhost:9090/ -c movies-api -s 10s --period=1440


import csv
import requests
import sys
import getopt
import time
import logging

PROMETHEUS_URL = ''
CONTAINER = ''
QUERY_API = '/api/v1/query'
RANGE_QUERY_API = '/api/v1/query_range'
RESOLUTION = '' # default: 10s
OUTPUTFILE = '' # default: result.csv
START = '' # rfc3339 | unix_timestamp
END = '' # rfc3339 | unix_timestamp
PERIOD = 60 # unit: minute, default 60

def main():
    handle_args(sys.argv[1:])

    metricnames = query_metric_names()
    print("Querying metric names succeeded, metric number: %s", len(metricnames))

    csvset = query_metric_values(metricnames=metricnames)
    print("Querying metric values succeeded, rows of data: %s", len(csvset))

    write2csv(metricnames=metricnames, dataset=csvset)

def handle_args(argv):
    global PROMETHEUS_URL
    global OUTPUTFILE
    global CONTAINER
    global RESOLUTION
    global START
    global END
    global PERIOD

    try:
        opts, args = getopt.getopt(argv, "h:o:c:s:", ["host=", "outfile=", "container=", "step=", "help", "start=", "end=", "period="])
    except getopt.GetoptError as error:
        logging.error(error)
        print_help_info()
        sys.exit(2)

    for opt, arg in opts:
        if opt == "--help":
            print_help_info()
            sys.exit()
        elif opt in ("-h", "--host"):
            PROMETHEUS_URL = arg
        elif opt in ("-o", "--outfile"):
            OUTPUTFILE = arg
        elif opt in ("-c", "--container"):
            CONTAINER = arg
        elif opt in ("-s", "--step"):
            RESOLUTION = arg
        elif opt == "--start":
            START = arg
        elif opt == "--end":
            END = arg
        elif opt == "--period":
            PERIOD = int(arg)

    if PROMETHEUS_URL == '':
        logging.error("You should use -h or --host to specify your prometheus server's url, e.g. http://prometheus:9090")
        print_help_info()
        sys.exit(2)
    elif CONTAINER == '':
        logging.error("You should use -c or --container to specify the name of the container which you want to query all the metrics of")
        print_help_info()
        sys.exit(2)

    if OUTPUTFILE == '':
        OUTPUTFILE = 'result.csv'
        #logging.warning("You didn't specify output file's name, will use default name %s", OUTPUTFILE)
    if RESOLUTION == '':
        RESOLUTION = '10s'
        logging.warning("You didn't specify query resolution step width, will use default value %s", RESOLUTION)
    if PERIOD == '' and START == '' and END == '':
        PERIOD = 10
        logging.warning("You didn't specify query period or start&end time, will query the latest %s miniutes' data as a test", PERIOD)

def print_help_info():
    print('')
    print('Metrics2CSV Help Info')
    print('    metrics2csv.py -h <prometheus_url> -c <container_name> [-o <outputfile>]')
    print('or: metrics2csv.py --host=<prometheus_url> --container=<container_name> [--outfile=<outputfile>]')
    print('---')
    print('Additional options: --start=<start_timestamp_or_rfc3339> --end=<end_timestamp_or_rfc3339> --period=<get_for_most_recent_period(int miniutes)>')
    print('                    use start&end or only use period')

def query_metric_names():
    response = requests.get(PROMETHEUS_URL + '/api/v1/label/__name__/values')
    status = response.json()['status']

    if status == "error":
        logging.error(response.json())
        sys.exit(2)
    
    results = response.json()['data']
    metricnames = list()
    for result in results:
        metricnames.append(result)
    metricnames.sort()
    print(metricnames)
    metricnames.remove('scrape_duration_seconds')
    metricnames.remove('scrape_samples_post_metric_relabeling')
    metricnames.remove('scrape_samples_scraped')
    metricnames.remove('scrape_series_added')     
    metricnames.remove('up')
    return metricnames


def query_metric_values(metricnames):
    csvset = dict()

    if PERIOD != '':
        end_time = int(time.time())
        start_time = end_time - 60 * PERIOD
    else:
        end_time = END
        start_time = START

    metric = metricnames[0]
    print(metric)
    response = requests.get(PROMETHEUS_URL + RANGE_QUERY_API, params={'query': metric, 'start': start_time, 'end': end_time, 'step': RESOLUTION})
    status = response.json()['status']
    print(status)
    if status == "error":
        logging.error(response.json())
        sys.exit(2)

    results = response.json()['data']['result']

    if len(results) == 0:
        logging.error(response.json())
        sys.exit(2)

    for value in results[0]['values']:
        csvset[value[0]] = [value[1]]

    for metric in metricnames[1:]:
        print(metric)
        response = requests.get(PROMETHEUS_URL + RANGE_QUERY_API, params={'query': metric, 'start': start_time, 'end': end_time, 'step': RESOLUTION})
        results = response.json()['data']['result']
        for value in results[0]['values']:
            csvset[value[0]].append(value[1])

    return csvset

def write2csv(metricnames, dataset):
    filename = time.strftime("%d-%m-%Y")+".csv"
    with open("data/"+filename, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(['timestamp'] + metricnames)
        for timestamp in sorted(dataset.keys(), reverse=True):
            writer.writerow([timestamp] + dataset[timestamp])
        # for line in dataset:
        #     writer.writerow([line] + dataset[line])

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
