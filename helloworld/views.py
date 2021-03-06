#!/usr/bin/env python
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from django.http import HttpResponse

from igramscraper.instagram import Instagram  # pylint: disable=no-name-in-module

from google.cloud import language_v1
from google.cloud.language_v1 import enums
from google.cloud import storage

from google.cloud import bigtable
from google.cloud.bigtable import column_family
from google.cloud.bigtable import row_filters

from google.cloud import bigquery

import datetime
import json
from dateutil import parser, tz
import datetime

data = []

def index(request):
    global data
    bq_client = bigquery.Client()
    dataset_id = 'jetblue'  # replace with your dataset ID
    table_id = 'jb_instagram'  # replace with your table ID
    table_ref = bq_client.dataset(dataset_id).table(table_id)
    table = bq_client.get_table(table_ref)  # API request
    errors = bq_client.insert_rows(table, data)  # API request
    print(errors)
    return HttpResponse(
        'Hello, World. This is Django running on Google App Engine')


def clear_table(request):
    bq_client = bigquery.Client()
    dataset_id = 'jetblue'  # replace with your dataset ID
    table_id = 'jb_instagram'  # replace with your table ID
    table_ref = bq_client.dataset(dataset_id).table(table_id)


def scrape(request):
    sc()
    return HttpResponse(
        'Jet Blue scraped on twitter')


def sc():
    instagram = Instagram()
    # instagram.with_credentials('username', 'password', 'path/to/cache/folder')
    # instagram.login()
    proxies = {
        'http': 'http://113.53.230.167',
        'http': 'http://115.110.129.134',
        'http': 'http://13.78.116.29',
        'http': 'http://185.57.164.167',
        'http': 'http://188.166.119.186',
    }

    medias = instagram.get_medias_by_tag('jetblue', count=1000)
    instagram.set_proxies(proxies)
    global data
    data = []
    i = 0
    bq_client = bigquery.Client()
    dataset_id = 'jetblue'  # replace with your dataset ID
    table_id = 'jb_instagram'  # replace with your table ID
    table_ref = bq_client.dataset(dataset_id).table(table_id)
    table = bq_client.get_table(table_ref)  # API request

    for media in medias:
        i+=1
        temp_data = []
        print("{} out of 1000".format(i))
        temp_data.append({"text": media.caption, "time": media.created_time})
        sample_analyze_sentiment(media.caption, temp_data[-1])
        sample_analyze_entities(media.caption, temp_data[-1])
        errors = bq_client.insert_rows(table, temp_data)  # API request
        data.append(temp_data[0])



    assert errors == []


def sample_analyze_entities(text_content, array_name):
    """
    Analyzing Entities in a String

    Args:
      text_content The text content to analyze
    """

    client = language_v1.LanguageServiceClient()
    type_ = enums.Document.Type.PLAIN_TEXT
    language = "en"
    document = {"content": text_content, "type": type_, "language": language}
    encoding_type = enums.EncodingType.UTF8

    response = client.analyze_entities(document, encoding_type=encoding_type)
    largest_salience = 0
    for entity in response.entities:
        if largest_salience < entity.salience:
            largest_salience = entity.salience
            array_name['keywords_name'] = format(entity.name)
            array_name['keywords_type'] = format(enums.Entity.Type(entity.type).name)
            # print(u"Salience score: {}".format(entity.salience))


def sample_analyze_sentiment(text_content, array_name):
    """
    Analyzing Sentiment in a String

    Args:
      text_content The text content to analyze
    """

    l_client = language_v1.LanguageServiceClient()

    type_ = enums.Document.Type.PLAIN_TEXT

    language = "en"
    document = {"content": text_content, "type": type_, "language": language}

    # Available values: NONE, UTF8, UTF16, UTF32
    encoding_type = enums.EncodingType.UTF8

    response = l_client.analyze_sentiment(document, encoding_type=encoding_type)
    # Get overall sentiment of the input document
    # print(u"Document sentiment score: {}".format(
     #    response.document_sentiment.score))
    array_name["sentiments"] = format(response.document_sentiment.score)


def analyze_twitter_json_delta(input_file):
    with open(input_file, encoding='utf-8', mode='r') as in_file:
        data = json.load(in_file)

        final_data = []
        for tweets in data["statuses"]:
            date = parser.parse(tweets['created_at'])
            date_num = (date-datetime.datetime(1970,1,1).replace(tzinfo=tz.tzutc())).total_seconds()

            final_data.append({"text": tweets['full_text'], "time": date_num})
            sample_analyze_sentiment(tweets['full_text'], final_data[-1])
            sample_analyze_entities(tweets['full_text'], final_data[-1])

        bq_client = bigquery.Client()
        dataset_id = 'delta'  # replace with your dataset ID
        table_id = 'd_twitter'  # replace with your table ID
        table_ref = bq_client.dataset(dataset_id).table(table_id)
        table = bq_client.get_table(table_ref)  # API request

        errors = bq_client.insert_rows(table, final_data)  # API request
        assert errors == []


def analyze_twitter_json_jetBlue(input_file):
    with open(input_file, encoding='utf-8', mode='r') as in_file:
        data = json.load(in_file)

        final_data = []
        for tweets in data["statuses"]:
            date = parser.parse(tweets['created_at'])
            date_num = (date-datetime.datetime(1970,1,1).replace(tzinfo=tz.tzutc())).total_seconds()

            final_data.append({"text": tweets['full_text'], "time": date_num})
            sample_analyze_sentiment(tweets['full_text'], final_data[-1])
            sample_analyze_entities(tweets['full_text'], final_data[-1])

        bq_client = bigquery.Client()
        dataset_id = 'jetblue'  # replace with your dataset ID
        table_id = 'jb_twitter'  # replace with your table ID
        table_ref = bq_client.dataset(dataset_id).table(table_id)
        table = bq_client.get_table(table_ref)  # API request

        errors = bq_client.insert_rows(table, final_data)  # API request
        assert errors == []
